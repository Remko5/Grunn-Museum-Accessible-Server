CREATE DATABASE groninger_museum;
use groninger_museum;

create table routes(
    ID int not null AUTO_INCREMENT PRIMARY KEY,
    name varchar(45) not null ,
    route MEDIUMTEXT
);