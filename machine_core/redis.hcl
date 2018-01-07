job "redis" {
  datacenters = ["dc1"]
  
  group "example" {
  count = 1
    task "server" {
      driver = "raw_exec"
      #env {
      #  redis_port = "6879"
      #}

      service {
        name = "redis"
        tags = ["machine", "core"]
        port = "redis_port"
        }

      config {
        #ver 4+ for plugins
        command = "redis-server"
        args = [
          "redis.conf",
          #"${my_key}"
          #"--port","${redis_port}"
        ]
      }
      template {
        data          =  "#uncomment and replace <user> with user name for local testing\n
        #or make /var/lib/redis user readable\n 
        #dir /home/<user>/db\n 
        #if uncommenting above line, comment below\n
        dir /var/lib/redis\n
        save 120 1\n
        port {{ env \"NOMAD_PORT_redis_port\" }}\n
        #bind 127.0.0.1\n
        #bind 192.168.0.155\n
        rename-command FLUSHDB ''\n
        rename-command FLUSHALL ''\n
        #rename-command KEYS ''\n
        rename-command PEXPIRE ''\n
        #rename-command DEL ''\n
        rename-command CONFIG '___.config.___.'\n
        rename-command SHUTDOWN ''\n
        rename-command BGREWRITEAOF ''\n
        rename-command BGSAVE ''\n
        rename-command SAVE ''\n
        rename-command SPOP ''\n
        rename-command SREM ''\n
        rename-command RENAME ''\n
        rename-command DEBUG ''\n
        #import for routing
        notify-keyspace-events KEA\n"
        #source        = "redis.conf.tpl"
        destination   = "redis.conf"
        change_mode   = "signal"
        change_signal = "SIGINT"
      }

      resources {
        network {
          #mbits = 10
          #port "http" {
          #  static = "5678"
          #}
          port "redis_port" {}
        }
      }
    }
  }
}
