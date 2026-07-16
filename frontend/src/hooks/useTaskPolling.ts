import type { TaskRecord } from "../types";

type TaskReader = (taskId: string) => Promise<TaskRecord>;

export async function pollTask(
  readTask: TaskReader,
  taskId: string,
  onUpdate: (task: TaskRecord) => void,
  maxAttempts = 60
): Promise<TaskRecord> {
  let current = await readTask(taskId);
  onUpdate(current);
  for (let attempt = 0; attempt < maxAttempts && ["queued", "running"].includes(current.status); attempt += 1) {
    await new Promise((resolve) => window.setTimeout(resolve, Math.min(5000, 250 * 2 ** Math.min(attempt, 5))));
    current = await readTask(taskId);
    onUpdate(current);
  }
  return current;
}
