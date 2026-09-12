# IntentTester TDL Sufficiency Audit Packet

This packet isolates four controlled semantic-collision pairs. Each pair keeps a
high-level test goal fixed and changes one clause that changes the valid target
adapter set.

The prompt renderer copies the public `IntentAbstractorAgent` prompt and TDL
format from IntentTester commit
`a906b7c49bbe0dec4d1d8b911e97281b7ce63063`. It performs no LLM call and therefore
does not claim an IntentTester result.

Run:

```bash
python3 benchmark/feasibility/intenttester/render_prompts.py
```

Then submit every JSONL row to the same configured model with fixed model name,
temperature, seed when supported, and three repeated runs. Store raw outputs and
model metadata before human clause-retention review. Reviewers receive only the
two TDL outputs; `cases.yaml` remains hidden until their judgments are frozen.

Current state: eight exact prompts are ready. Actual outputs remain pending
because the official artifact requires a DashScope API key and model name that
are not present in the current environment.
# 发布说明

原始 TDL prompt/schema 的再分发许可尚未确认，因此对应的本地渲染脚本、schema 副本及生成请求不包含在公开仓库。以下历史步骤以另行取得合法上游材料为前提，不表示当前 checkout 自带完整 TDL 提取环境。
