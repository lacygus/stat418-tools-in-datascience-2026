# Sungjin Choi - Final Project Submission

**Project:** Soccer Player Market Value Prediction

## Links

- **GitHub repo:** https://github.com/lacygus/418_final
- **Web app (Streamlit Cloud):** https://418final-uxdflcbiixufvv9rpxytej.streamlit.app/
- **Prediction API (Google Cloud Run):** https://market-value-api-348858993647.us-central1.run.app
- **API docs (Swagger UI):** https://market-value-api-348858993647.us-central1.run.app/docs

## Summary

A scouting tool that predicts a player's market value from public match
stats and explains each prediction with SHAP. RandomForest regressor on
log(market_value), trained on 2,013 players across the top 5 European
leagues. Test R² = 0.59, MAE = $9.6M. Streamlit web app calls a deployed
FastAPI service on Cloud Run for parity.
