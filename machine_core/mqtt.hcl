job "mqtt" {
  datacenters = ["dc1"]
  
  group "example" {
  count = 1
    task "server" {
      driver = "raw_exec"
      #env {
      #  redis_port = "6879"
      #}

      service {
        name = "mqtt"
        tags = ["machine", "core"]
        port = "mqtt_port"
        }

      config {
        command = "mosquitto"
        args = [
          "-c","mosquitto.conf",
          #"--port","${redis_port}"
        ]
      }
      template {
        data          =  "port {{ env \"NOMAD_PORT_mqtt_port\" }}\n#bind 127.0.0.1 192.168.0.155\n"
        #source        = "redis.conf.tpl"
        destination   = "mosquitto.conf"
        change_mode   = "signal"
        change_signal = "SIGINT"
      }

      resources {
        network {
          #mbits = 10
          #port "http" {
          #  static = "5678"
          #}
          port "mqtt_port" {}
        }
      }
    }
  }
}