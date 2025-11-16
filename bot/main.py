from script import client
import attack
import save
import replier
import cleanup
import cvm


print("Connecting...")
client.start()
print("Logged in as user✔️")
client.run_until_disconnected()

