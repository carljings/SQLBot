module.exports = {
  apps: [
    {
      name: 'backend',
      script: '/Users/guchuan/.local/bin/uv',
      args: 'run uvicorn main:app --reload --host 0.0.0.0 --port 8000',
      cwd: './backend',
      interpreter: 'none',
      env_file: './backend/.env',
    },
    {
      name: 'frontend',
      script: 'npm',
      args: 'run dev',
      cwd: './frontend',
      interpreter: 'none',
    },
    {
      name: 'g2-ssr',
      script: 'app.js',
      cwd: './g2-ssr',
    },
    {
      name: 'dashboard',
      script: './pm2-dashboard.js',
      interpreter: 'node',
    },
  ],
}
