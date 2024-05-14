#!/bin/bash
apt -y install postgresql-14
systemctl enable postgresql.service
systemctl start postgresql.service
echo "Введите новый пароль базы данных\n"
passwd postgres