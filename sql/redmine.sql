CREATE ROLE redmine LOGIN ENCRYPTED PASSWORD '%pwd%' NOINHERIT VALID UNTIL 'infinity';
CREATE DATABASE redmine WITH ENCODING='UTF8' OWNER=redmine;