rdb-fullstack
=============
This project involves two small projects which aimed at Relational Databases and Full Stack Fundamentals courses

1. tournament
=============
This project provides swiss tournament pairs given by the corresponding standings.

What's included:
All the related code is under the tournament.
The tournament.sql creates Match table, Player table, and Standing view to store and display the data.
The tournament.py provides the necessary basic operations.

  tournament/
  |-- tournament_test.py
  |—- tournament.py
  |—- tournament.sql

2. Catalog
=============
This is a small website which supports create, read, update and delete items as well as oath 2.0 authorization.

What's included:
All the related code is under the project.
The folder templates contains the html pages of this project.
The folder static contians the style sheet of this project.
database_setup.py contains the database sql.
main.py is the backend server logic.

How to start:
1. Install Vagrant and VirtualBox
2. Clone the fullstack-nanodegree-vm
3. Launch the Vagrant VM (vagrant up)
4. Run the application within the VM (python /vagrant/project/main.py)
5. Access the application by visiting http://localhost:8000 locally

