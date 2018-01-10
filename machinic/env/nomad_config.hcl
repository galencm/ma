log_level = "DEBUG"
#data_dir = "/home/$USER/.local/nomad_data"
data_dir = "/var/lib/nomad/data"
enable_debug = true
name = "client1"
server {
  enabled          = true
  bootstrap_expect = 1
}
client {
    enabled = true
    #servers = ["127.0.0.1:4647"]
    #node_class = "foo"
    options {
        "driver.raw_exec.enable" = "1"
    }
}

