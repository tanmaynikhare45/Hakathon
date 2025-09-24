import os
from app import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    # i thibk all files are working prperly
    #the projrct name civiv eye is worki g prperlyin my laptop

    
    app.run(host="0.0.0.0", port=port, debug=True)
    







    