import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const webDirectory = path.dirname(fileURLToPath(import.meta.url));
const projectDirectory = path.resolve(webDirectory, "..");
const localPython = path.join(
  projectDirectory,
  ".venv-dashboard",
  "Scripts",
  "python.exe",
);
const pythonCommand = process.env.PYTHON || (existsSync(localPython) ? localPython : "python");

const services = [
  {
    name: "CSV API",
    command: pythonCommand,
    args: [path.join(projectDirectory, "servidor_dashboard.py")],
    cwd: projectDirectory,
  },
  {
    name: "Vite",
    command: process.execPath,
    args: [
      path.join(webDirectory, "node_modules", "vite", "bin", "vite.js"),
      "--host",
      "127.0.0.1",
      ...process.argv.slice(2),
    ],
    cwd: webDirectory,
  },
];

const children = [];
let stopping = false;

function stopChildren() {
  if (stopping) return;
  stopping = true;
  for (const child of children) {
    if (!child.killed) child.kill();
  }
}

for (const service of services) {
  const child = spawn(service.command, service.args, {
    cwd: service.cwd,
    stdio: "inherit",
  });
  children.push(child);
  child.on("error", (error) => {
    console.error(`${service.name} no pudo iniciarse: ${error.message}`);
    stopChildren();
    process.exitCode = 1;
  });
  child.on("close", (code) => {
    if (!stopping) {
      console.error(`${service.name} se detuvo. Cerrando los demás servicios.`);
      stopChildren();
      process.exitCode = code || 1;
    }
  });
}

process.on("SIGINT", () => {
  stopChildren();
  process.exitCode = 130;
});

process.on("SIGTERM", stopChildren);
