# LinkedIn Post: relay-plugin Open Source Release

## English Version (Main Post)

---

🚀 **Open-Sourcing a Multi-Agent Team Framework for Claude Code**

I'm excited to share **relay-plugin**, a framework that enables Claude Code's Agent Teams to orchestrate multiple AI models through CLI-based invocation.

**The Problem:**
Building multi-agent systems with Claude Code is powerful, but hitting API usage limits can bring your entire team to a halt. We needed a way to distribute work across multiple providers without sacrificing coordination.

**Key Features:**

🔹 **CLI-Based External Model Invocation**
- Direct CLI calls to `codex`, `gemini`, `zai` without MCP dependencies
- Cleaner architecture, lower latency, simpler deployment

🔹 **Claude Usage Limit Bypass**
- Switch coordinator from Claude to GLM (Zhipu AI) via environment variable
- Your team keeps running even when Claude quota is exhausted

🔹 **Phase-Based Routing**
```
probe  → Research & requirements (codex)
grasp  → Architecture & design (codex)
tangle → Implementation (codex-spark for speed)
ink    → Review & deployment (codex-spark)
```

🔹 **Smart Provider Routing**
- `round-robin`: Distribute load evenly
- `fastest`: Route to lowest latency provider
- `cheapest`: Optimize for cost

🔹 **Automatic Fallback Chain**
```
codex → codex-spark → gemini-fast → zai
```

**Architecture:**
```
┌─────────────────────────────────────┐
│  Coordinator (Claude or GLM)        │
│  - Workflow orchestration           │
│  - Inter-agent communication        │
└──────────────┬──────────────────────┘
               │ SendMessage
      ┌────────┼────────┐
      ▼        ▼        ▼
   codex    gemini    zai
   (code)  (analysis) (general)
```

**Supported CLI Variants:**

| CLI | Model | Use Case | Latency |
|-----|-------|----------|---------|
| codex | gpt-5.3-codex | Flagship code gen | 1200ms |
| codex-spark | gpt-5.3-codex-spark | Fast reviews (15x) | 300ms |
| gemini | gemini-3-pro-preview | Research, multimodal | 800ms |
| gemini-fast | gemini-3-flash-preview | Real-time processing | 400ms |
| claude-opus | claude-opus-4-6 | Strategic reasoning | 3000ms |
| zai | glm-4-air | Cost-effective general | 500ms |

**Result:** Reduced Claude API usage by ~70% while maintaining team coordination quality.

🔗 **GitHub:** github.com/yarang/relay-plugin

Feedback and contributions welcome! 🙏

---

## Korean Summary (Append to Post)

---

**[한국어 요약]**

Claude Code의 Agent Teams 기능을 확장하여 다양한 AI 모델을 하나의 팀으로 orchestrate하는 프레임워크를 오픈소스로 공개합니다.

주요 특징:
- MCP 없이 CLI로 외부 모델 직접 호출 (codex, gemini, zai)
- GLM 코디네이터로 전환하여 Claude 사용량 한계 회피
- Phase별 자동 모델 라우팅 (연구/설계/구현/리뷰)
- 지연시간/비용 기반 스마트 라우팅
- 자동 Fallback 체인으로 고가용성 보장

Claude API 사용량을 약 70% 절감하면서도 팀 운영 품질을 유지할 수 있었습니다.

GitHub: github.com/yarang/relay-plugin

---

## Hashtags

```
#ClaudeCode #MultiAgent #AI #LLM #OpenSource #AgentTeams #ArtificialIntelligence #DeveloperTools #AIOrchestration
```

## Posting Checklist

- [ ] Replace `github.com/yarang/relay-plugin` with actual repository URL
- [ ] Add screenshot of architecture diagram (optional)
- [ ] Tag relevant people/companies (Anthropic, OpenAI, Google, Zhipu AI)
- [ ] Schedule for optimal engagement time (Tue-Thu, 9-11 AM)
