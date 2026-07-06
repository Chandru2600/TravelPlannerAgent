web: gunicorn -b 0.0.0.0:$PORT "app:create_app('production')"
streamlit: streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0
