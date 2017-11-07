DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DB_DIR=/var/lib/redis

#Install the Build and Test Dependencies
sudo apt-get update
sudo apt-get install build-essential tcl curl

#Download, Compile, and Install Redis
cd /tmp
curl -O http://download.redis.io/redis-stable.tar.gz
tar xzvf redis-stable.tar.gz
cd redis-stable
make
make test
sudo make install

#Configure Redis
sudo rm -rf /etc/redis
sudo mkdir /etc/redis
sudo cp $DIR/redis.conf /etc/redis

#Create a Redis systemd Unit File
sudo cp $DIR/redis.service /etc/systemd/system/redis.service

#Create the Redis User, Group and Directories
sudo adduser --system --group --no-create-home redis
sudo rm -rf $DB_DIR
sudo mkdir $DB_DIR
sudo chown redis:redis $DB_DIR
sudo chmod 770 $DB_DIR

#Start Redis
sudo systemctl start redis

#Enable Redis to Start at Boot
sudo systemctl enable redis
