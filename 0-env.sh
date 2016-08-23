mkdir /home/luis/abb/events/
mkdir /home/luis/abb/preproc/
mkdir /home/luis/abb/sessions
mkdir /home/luis/abb/users/

split -l 200000 /home/luis/abb/export-2015-10-23/tinyevents.csv /home/luis/abb/events/events