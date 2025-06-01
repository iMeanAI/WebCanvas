mkdir -p dataset_4o

rm -rf dataset_4o/*

python utils/parser.py
python utils/dataset_process.py