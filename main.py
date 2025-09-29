import os
from app import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    
    #before running the database cheaak the ip address is active or not active ip address then run

    
    app.run(host="0.0.0.0", port=port, debug=True)
    







    