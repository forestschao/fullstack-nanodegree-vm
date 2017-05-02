-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.
DROP DATABASE IF EXISTS tournament;

CREATE DATABASE tournament;
\c tournament

CREATE TABLE Player(
    id	 SERIAL PRIMARY KEY NOT NULL,
    name TEXT               NOT NULL
);

CREATE TABLE Match(
    id     SERIAL PRIMARY KEY       NOT NULL,
    winner INT    REFERENCES Player NOT NULL,
    loser  INT    REFERENCES Player NOT NULL
);

CREATE VIEW Standing
AS
SELECT Player.id,
       Player.name,
       COALESCE(Win.win, 0) AS win,
       COALESCE(Loss.loss, 0) AS loss
FROM Player
LEFT JOIN (
           SELECT winner   AS player,
                  COUNT(*) AS win
           FROM Match
           GROUP BY winner
    ) AS Win
ON Player.id = Win.player

LEFT JOIN (
          SELECT loser    AS player,
                 COUNT(*) AS loss
          FROM Match
          GROUP BY loser
   ) AS Loss
ON Player.id = Loss.player
ORDER BY win DESC;

-- Test case
INSERT INTO Player(name) VALUES('test1');
INSERT INTO Player(name) VALUES('test2');
INSERT INTO Player(name) VALUES('test3');
INSERT INTO Player(name) VALUES('test4');

INSERT INTO Match(winner, loser) VALUES(1,2);
INSERT INTO Match(winner, loser) VALUES(3,4);
INSERT INTO Match(winner, loser) VALUES(1,3);
INSERT INTO Match(winner, loser) VALUES(4,2);
