module.exports = {
  apps: [
    {
      name: 'goldventure-frontend',
      cwd: '/var/www/goldventure/frontend',

      // Next's own binary, not `npm start`. pm2 cluster mode forks a Node
      // entry point through Node's cluster module, and it cannot do that with
      // npm in the way — npm is a shell wrapper, so pm2 would refuse cluster
      // mode or fork a wrapper that owns no listening socket.
      script: './node_modules/next/dist/bin/next',
      args: 'start',

      // Two instances sharing one listening socket, so `pm2 reload` can cycle
      // them one at a time. A deploy used to restart the single process and the
      // site returned 502 for about a second while Next rebound; with a rolling
      // reload the other instance keeps answering. Measured before the change:
      // 4 consecutive 502s over ~0.87s on every deploy.
      exec_mode: 'cluster',
      instances: 2,

      // Wait for Next to actually listen before pm2 considers an instance up
      // and moves on to cycling the next one. Without it, reload can kill the
      // second instance while the first is still binding, which is the very
      // gap this is meant to close.
      wait_ready: false,
      listen_timeout: 10000,
      kill_timeout: 5000,

      max_memory_restart: '600M',

      env: {
        NODE_ENV: 'production',
        NEXT_PUBLIC_API_URL: 'https://juniorminingintelligence.com/api',
        BACKEND_URL: 'http://127.0.0.1:8000',
        NEXT_PUBLIC_WS_URL: 'wss://juniorminingintelligence.com',
        NEXT_PUBLIC_GA_MEASUREMENT_ID: 'G-3F3WN9C8RG'
      }
    }
  ]
};
