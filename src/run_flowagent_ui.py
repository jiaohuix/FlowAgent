""" 
> streamlit run run_flowagent_ui.py
streamlit run run_flowagent_ui.py --server.address 0.0.0.0 --server.port=8502 -- --config=default.yaml
"""
import argparse
from flowagent.ui.app import main

if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--config", type=str, default="default.yaml")
    args = args.parse_args()
    main(args.config)
