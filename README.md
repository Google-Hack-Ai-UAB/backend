# backend

## How to Run

`make build up`

* Configure the .env file accordingly

``` Python
PINECONE_API_KEY = 'bb34fa83-7693-4d31-888e-a0865eccaedf'
PINECONE_ENV = 'us-west1-gcp-free'
GOOGLE_APPLICATION_CREDENTIALS = 'yyy.json'
MONGO_URL="mongodb+srv://userstorer:youwillneverguessthispassword@aihack.89so8jl.mongodb.net/?retryWrites=true&w=majority&appName=AIHack"
```


## Tools Used
* **FASTapi**: Web framework for building API endpoints
* **Uvicorn**: Webserver used to host the API
* **Dotenv**: Secret managment tool used to store secrets like the MongoDB connection string
* **Docker**: Containerization platform used to run the backend in an isolated enviornment

