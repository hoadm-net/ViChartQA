---
trigger: always_on
---

## Core Rules

1. **Current Directory Isolation (🔴 Critical)**

   - The agent MUST operate strictly within the current workspace project directory passed by the active document or user context.
   - When working on `Research/ViChartQA`, the agent MUST NEVER read, write, modify, or execute commands in `Intern`, and vice-versa.
   - Do not create temporary files, debug scripts, or tests in a project directory that is different from the target project directory.
2. **Direct Shell Execution**

   - For Git operations, file cleanups, and typical command execution, execute direct shell commands using `ctx_shell` instead of writing temporary Python/bash scripts.
   - Only write scripts if a programmatic flow is explicitly required (e.g. executing complex integration test logic).
3. **Workspace Boundary**

   - Strictly check paths before running commands. All `Cwd` parameters in tool calls must reside within the target project's path.
   - Always use venv environment.
4. **Temporary & Test Files Isolation**

   - During task execution, any test scripts, test outputs, or temporary files MUST be saved strictly in the `test` directory.
   - When the task is finished, you must completely delete these temporary/test files, EXCEPT for those test files that have long-term reusable value.
