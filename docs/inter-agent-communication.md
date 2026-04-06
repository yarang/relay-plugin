# Inter-Agent Communication Architecture

> **참고**: 이 문서는 Claude Code 내부 멀티에이전트 통신 아키텍처의 기술 참조 자료입니다.  
> relay-plugin의 teammate / subagent 실행 모드 설계의 근거로 활용됩니다.  
> 원본이 영어로 작성되어 있으므로 이 문서는 영어로 유지됩니다.

> Multi-agent messaging, team coordination, and agent lifecycle in Claude Code's swarm system.

---

## High-Level Overview

Claude Code implements a multi-agent system (called "swarms") where a team lead orchestrates multiple teammate agents to work in parallel. The communication architecture is built on a **file-based message bus** with **mailbox-style inboxes**, supporting both in-process and out-of-process agents.

```
┌─────────────────────────────────────────────────────────┐
│  Team Lead (current Claude session)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │ TeamCreateTool│  │SendMessageTool│  │   AppState    │ │
│  └──────┬────────┘  └──────┬───────┘  └───────────────┘ │
└─────────┼──────────────────┼──────────────────────────────┘
          │                  │
    ┌─────▼──────┐    ┌─────▼──────┐
    │ config.json │    │  Mailbox    │  ← File-based message bus
    │ (team state)│    │ (inboxes/)  │    (locking + polling)
    └─────┬──────┘    └─────┬──────┘
          │                  │
    ┌─────▼──────────────────▼──────┐
    │         Teammates             │
    │  ┌────────────┐ ┌───────────┐ │
    │  │ In-Process │ │ tmux Pane │ │
    │  │ (direct)   │ │ (polling) │ │
    │  └────────────┘ └───────────┘ │
    └───────────────────────────────┘
```

---

## Layer 1: Team Management

### Team Creation

`TeamCreateTool` creates a team with the following structure:

```
~/.claude/teams/{team_name}/config.json   ← Team configuration file
~/.claude/tasks/{team_name}/               ← Shared task list directory
```

**TeamFile schema** (`src/utils/swarm/teamHelpers.ts`):

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | Team name |
| `description` | `string?` | Team purpose |
| `createdAt` | `number` | Timestamp |
| `leadAgentId` | `string` | Leader's deterministic agent ID |
| `leadSessionId` | `string?` | Leader's session ID for discovery |
| `members` | `Member[]` | Array of team members |
| `hiddenPaneIds` | `string[]?` | Panes hidden from UI |

**Member schema**:

| Field | Type | Description |
|-------|------|-------------|
| `agentId` | `string` | Format: `name@teamName` |
| `name` | `string` | Human-readable name |
| `agentType` | `string?` | Role type |
| `model` | `string?` | LLM model |
| `tmuxPaneId` | `string` | Terminal pane ID |
| `cwd` | `string` | Working directory |
| `worktreePath` | `string?` | Git worktree path |
| `backendType` | `string?` | `in-process` or `tmux` |
| `isActive` | `boolean?` | Active status flag |
| `mode` | `PermissionMode?` | Current permission mode |

### Constraints

- One team per leader session
- Team name uniqueness enforced (auto-generates slug on collision)
- Session cleanup registered via `registerTeamForSessionCleanup()`
- Task numbering starts fresh at 1 for each team

### Key Operations

| Operation | Function | Sync/Async |
|-----------|----------|------------|
| Read team file | `readTeamFile()` / `readTeamFileAsync()` | Both |
| Write team file | `writeTeamFile()` / `writeTeamFileAsync()` | Both |
| Remove teammate | `removeTeammateFromTeamFile()` | Sync |
| Set member active | `setMemberActive()` | Async |
| Set member mode | `setMemberMode()` | Sync |
| Batch mode update | `setMultipleMemberModes()` | Sync |
| Cleanup on exit | `cleanupSessionTeams()` | Async |

---

## Layer 2: Mailbox Message Bus

### Storage Layout

Each agent gets an inbox file on disk:

```
~/.claude/teams/{team_name}/inboxes/{agent_name}.json
```

The file contains a JSON array of `TeammateMessage` objects:

```typescript
interface TeammateMessage {
  from: string        // sender name
  text: string        // message content (plain text or JSON)
  timestamp: string   // ISO timestamp
  read: boolean       // read status
  color?: string      // sender color
  summary?: string    // 5-10 word preview
}
```

### Write Protocol

`writeToMailbox()` in `src/utils/teammateMailbox.ts` follows this sequence:

1. Create inbox directory if missing (`mkdir -p`)
2. Create inbox file if missing (atomic `wx` flag)
3. Acquire file lock via `proper-lockfile` (10 retries, 5-100ms backoff)
4. Re-read file after locking (prevent stale-read races)
5. Append new message with `read: false`
6. Write entire array back and release lock

### Read Protocol

- `readMailbox()` — reads full inbox from disk
- `readUnreadMessages()` — filters for `read === false`
- `markMessagesAsRead()` — batch marks all as read
- `markMessageAsReadByIndex()` — marks single message
- `markMessagesAsReadByPredicate()` — conditional marking
- `clearMailbox()` — empties inbox (only if file exists)

### Message Types

The mailbox carries both plain-text messages and structured protocol messages:

| Type | Direction | Purpose |
|------|-----------|---------|
| Plain text | Any → Any | Free-form agent communication |
| `idle_notification` | Worker → Leader | Worker finished a turn |
| `shutdown_request` | Leader → Worker | Request graceful termination |
| `shutdown_approved` | Worker → Leader | Confirm shutdown |
| `shutdown_rejected` | Worker → Leader | Refuse shutdown with reason |
| `plan_approval_request` | Worker → Leader | Request plan approval |
| `plan_approval_response` | Leader → Worker | Approve/reject plan |
| `permission_request` | Worker → Leader | Tool-use permission escalation |
| `permission_response` | Leader → Worker | Permission decision |
| `task_assignment` | Leader → Worker | Task assignment notification |
| `team_permission_update` | Leader → Workers | Broadcast permission rule changes |
| `mode_set_request` | Leader → Worker | Change teammate permission mode |

### Structured Message Detection

`isStructuredProtocolMessage()` checks if a message is a typed protocol message. These are intercepted by the inbox poller and routed to specific handlers — they are never shown as raw JSON to the LLM.

### Message Formatting

`formatTeammateMessages()` wraps messages in XML tags (`<teammate_message>`) for injection into the conversation as context attachments.

---

## Layer 3: Agent Spawning

`spawnTeammate()` in `src/tools/shared/spawnMultiAgent.ts` supports three spawn strategies:

### Strategy 1: In-Process

Used when `isInProcessEnabled()` is true (feature flag or auto-fallback).

```
Leader → spawnInProcessTeammate()
       → AsyncLocalStorage context created
       → startInProcessTeammate() (direct call)
       → No mailbox needed for initial prompt
```

- Teammates share the same Node.js process
- Context isolation via `AsyncLocalStorage`
- Prompt passed directly (no mailbox write)
- Faster communication, lower overhead

### Strategy 2: tmux Split Pane

Default pane-based spawn (tmux or iTerm2 native split).

```
Leader → detectAndGetBackend()
       → createTeammatePaneInSwarmView()
       → Build CLI command with --agent-id, --agent-name, --team-name, etc.
       → Send command to new pane
       → writeToMailbox() with initial prompt
       → Teammate boots → inbox poller starts → receives prompt
```

- Separate terminal pane with its own Claude Code process
- Communicates exclusively via mailbox polling
- Layout: leader on left (30%), teammates on right (70%)

### Strategy 3: tmux Separate Window

Legacy behavior — creates a new tmux window per teammate.

- Similar flow to split pane
- Creates window in `claude-swarm` session
- Also uses mailbox for initial prompt delivery

### Spawn Dispatch Logic

```
handleSpawn(input, context)
  → if isInProcessEnabled():
      handleSpawnInProcess()
  → else try detectAndGetBackend():
      → on failure in 'auto' mode:
          fallback to handleSpawnInProcess()
      → on success:
          handleSpawnSplitPane() or handleSpawnSeparateWindow()
```

### Inherited CLI Flags

Teammates inherit these flags from the leader:

- `--dangerously-skip-permissions` (unless `planModeRequired`)
- `--model`
- `--settings`
- `--plugin-dir`
- `--chrome` / `--no-chrome`

---

## Layer 4: Identity Resolution

`src/utils/teammate.ts` resolves "who am I?" using a priority chain:

```
Priority 1: AsyncLocalStorage context  (in-process teammates)
Priority 2: dynamicTeamContext          (CLI flags: --agent-id, --agent-name, --team-name)
Priority 3: AppState.teamContext        (team lead)
```

### Key Functions

| Function | Returns | Purpose |
|----------|---------|---------|
| `getAgentId()` | `string?` | Current agent ID |
| `getAgentName()` | `string?` | Current agent name |
| `getTeamName(teamContext?)` | `string?` | Current team name |
| `isTeammate()` | `boolean` | Is current session a teammate |
| `isTeamLead(teamContext)` | `boolean` | Is current session the team lead |
| `getTeammateColor()` | `string?` | UI display color |
| `isPlanModeRequired()` | `boolean` | Must enter plan mode before code |
| `getParentSessionId()` | `string?` | Leader's session ID |

### Team Lead Detection

A session is the team lead if:
- Its agent ID matches `teamContext.leadAgentId`, OR
- No agent ID is set but a team context exists (backwards compatibility)

---

## Layer 5: Message Routing

`SendMessageTool` in `src/tools/SendMessageTool/SendMessageTool.ts` is the central routing hub.

### Routing Decision Tree

```
SendMessage(to, message)
  │
  ├── to: "bridge:{session-id}" ──→ postInterClaudeMessage()   [cross-session]
  ├── to: "uds:{socket-path}" ────→ sendToUdsSocket()          [Unix socket]
  │
  ├── message is string:
  │   ├── to: "*" ──────────────→ handleBroadcast()
  │   │                           → writeToMailbox() for each teammate
  │   │
  │   └── to: "{name}" ────────→ check agentNameRegistry
  │       ├── Running in-process → queuePendingMessage()       [memory queue]
  │       ├── Stopped in-process → resumeAgentBackground()     [auto-resume]
  │       ├── No task, has name  → resumeAgentBackground()     [resume from transcript]
  │       └── Not in registry ──→ handleMessage()              [mailbox write]
  │
  └── message is structured:
      ├── shutdown_request ──────→ handleShutdownRequest()
      ├── shutdown_response:
      │   ├── approve ───────────→ handleShutdownApproval()    [exit agent]
      │   └── reject ────────────→ handleShutdownRejection()   [continue]
      └── plan_approval_response:
          ├── approve ───────────→ handlePlanApproval()        [team lead only]
          └── reject ────────────→ handlePlanRejection()       [team lead only]
```

### Broadcast Behavior

When `to: "*"`:
1. Read team file to get all members
2. Skip sender
3. Write to each recipient's mailbox
4. Return recipient list

### Auto-Resume of Stopped Agents

When a message targets a stopped agent:
1. Check `agentNameRegistry` for the agent ID
2. Look up task in `AppState.tasks`
3. If task is stopped (not running), call `resumeAgentBackground()`
4. The agent resumes with the incoming message as its new prompt
5. Output is written to a background file; leader is notified on completion

---

## Task Lifecycle

### LocalAgentTask (`src/tasks/LocalAgentTask/`)

Background agents with full lifecycle management.

**State fields:**

| Field | Description |
|-------|-------------|
| `agentId` | Unique agent identifier |
| `prompt` | Original prompt |
| `abortController` | Cancellation signal |
| `pendingMessages` | Queue for mid-turn SendMessage delivery |
| `isBackgrounded` | Running in background |
| `progress` | Tool count, token count, recent activities |
| `evictAfter` | Grace period timestamp for UI removal |

**Lifecycle:**

```
registerAsyncAgent() → running → completeAgentTask() / failAgentTask()
                                    ↓
                          evictAfter grace period → removed from state
```

**Message delivery:**
- `queuePendingMessage()` — append to pending queue
- `drainPendingMessages()` — atomic read-and-clear at tool-round boundaries
- Messages injected into agent's API input during the next tool round

### InProcessTeammateTask (`src/tasks/InProcessTeammateTask/`)

In-process teammates with cooperative shutdown.

**State fields:**

| Field | Description |
|-------|-------------|
| `identity` | `{ agentId, agentName, teamName, color, planModeRequired }` |
| `pendingUserMessages` | Message queue for the teammate |
| `messages` | Conversation history (capped) |
| `shutdownRequested` | Cooperative shutdown flag |
| `currentWorkAbortController` | Abort current turn without killing teammate |

**Lifecycle:**

```
spawn → running ⇄ idle cycle → shutdownRequested → killed
```

**Message injection:**
- `injectUserMessageToTeammate()` — primary injection for zoomed view
- Appends to `pendingUserMessages` for API input routing
- Also appends to `messages` for transcript display

---

## Shutdown Protocol

Graceful shutdown follows a request-response pattern:

```
Leader                              Teammate
  │                                     │
  │─── shutdown_request ──────────────→ │
  │                                     │
  │          (teammate checks            │
  │           if safe to exit)           │
  │                                     │
  │←── shutdown_approved ──────────────│  (exit: abort controller / process)
  │   or                                │
  │←── shutdown_rejected ──────────────│  (continue: reason provided)
```

For in-process teammates:
- Approval triggers `abortController.abort()` on the task
- The agent loop detects the abort and exits cleanly

For out-of-process teammates:
- Approval triggers `gracefulShutdown(0)` via `setImmediate()`
- The separate process exits

---

## Plan Approval Protocol

Teammates in plan mode must get approval before implementing:

```
Teammate                            Leader
  │                                   │
  │─── plan (presented as output) ──→ │
  │                                   │
  │          (leader reviews           │
  │           and decides)             │
  │                                   │
  │←── plan_approval_response ───────│
  │     approved: true/false          │
  │     permissionMode: inherited     │
  │     feedback: string (if rejected)│
```

Only the team lead can approve or reject plans. Teammates cannot approve their own plans.

---

## Cross-Session Communication

### Bridge (Remote Control)

Messages to `bridge:{session-id}` use Anthropic's servers to relay prompts between Claude sessions on potentially different machines.

- Requires explicit user consent (safety check, bypass-immune)
- Only plain text messages (no structured protocol)
- Requires active ReplBridge connection
- `postInterClaudeMessage()` handles delivery

### Unix Domain Socket (UDS)

Messages to `uds:{socket-path}` use local Unix sockets for same-machine inter-process communication.

- Plain text only
- `sendToUdsSocket()` handles delivery
- Summary not required (not rendered in UI for string messages)

---

## Visual Layout

### Pane Management

`teammateLayoutManager.ts` manages the visual arrangement:

| Environment | Backend | Layout |
|-------------|---------|--------|
| Inside tmux | TmuxBackend | Split current window (30/70) |
| iTerm2 (no tmux) | ITermBackend | Native iTerm2 split |
| Plain terminal | TmuxBackend | External `claude-swarm` session |

### Color Assignment

`assignTeammateColor()` assigns colors from a palette in round-robin order, persisted in an in-memory Map for the session duration. Colors are cleared on team cleanup.

---

## Key Design Decisions

### Why File-Based Messaging?

- Cross-process: tmux/iTerm2 teammates run in separate processes with no shared memory
- Reliability: file system is the only IPC mechanism guaranteed across all backends
- Crash recovery: messages persist on disk if a process crashes
- Simplicity: no message broker dependency

### Why Dual Backend (In-Process + Out-of-Process)?

- **In-process**: Lower latency, no mailbox overhead, direct function calls. Ideal for fast parallel work.
- **Out-of-process**: Full isolation, separate terminal panes visible to user, crash isolation. Traditional swarm experience.
- **Auto-fallback**: If tmux/iTerm2 detection fails in auto mode, seamlessly falls back to in-process.

### Why Cooperative Shutdown?

- Agents may be mid-turn (executing tools, writing files)
- Forced termination could leave files in inconsistent states
- Request-response protocol gives agents a chance to finish current work
- Rejection allows agents to explain why they can't stop yet

---

## File Reference

| File | Purpose |
|------|---------|
| `src/tools/TeamCreateTool/TeamCreateTool.ts` | Team creation and registration |
| `src/tools/SendMessageTool/SendMessageTool.ts` | Message routing hub |
| `src/tools/shared/spawnMultiAgent.ts` | Teammate spawning strategies |
| `src/utils/teammateMailbox.ts` | Mailbox read/write with file locking |
| `src/utils/teammate.ts` | Identity resolution |
| `src/utils/swarm/teamHelpers.ts` | Team file management |
| `src/utils/swarm/constants.ts` | Swarm constants (names, env vars) |
| `src/utils/swarm/teammateLayoutManager.ts` | Visual pane management |
| `src/tasks/LocalAgentTask/LocalAgentTask.tsx` | Background agent lifecycle |
| `src/tasks/InProcessTeammateTask/InProcessTeammateTask.tsx` | In-process teammate lifecycle |
