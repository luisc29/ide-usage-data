mkdir /abb/events/
mkdir /abb/preproc/
mkdir /abb/sessions
mkdir /abb/users/

mkdir /udc/users/

split -l 200000 /abb/export-2015-10-23/tinyevents.csv /home/luis/abb/events/events

pip install numpy
pip install pandas
pip install scipy
pip install sklearn
