# MongoDB Setup Guide

## Installing MongoDB

### For Ubuntu/Debian:
```bash
# Import MongoDB public GPG key
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Update package database
sudo apt-get update

# Install MongoDB
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
```

### For macOS:
```bash
# Using Homebrew
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB
brew services start mongodb-community
```

### For Windows:
1. Download MongoDB Community Server from https://www.mongodb.com/try/download/community
2. Run the installer
3. Choose "Complete" installation
4. Install MongoDB as a service
5. MongoDB Compass will be installed as GUI tool

## Verifying Installation

```bash
# Check MongoDB is running
mongosh

# In MongoDB shell
show dbs
```

## Creating Database and Collections

The application will automatically create the database and collections when you run:

```bash
php artisan db:seed
```

However, you can manually create them:

```javascript
// Connect to MongoDB shell
mongosh

// Switch to database
use travel_recommendation

// Create collections
db.createCollection("users")
db.createCollection("tours")
db.createCollection("recommendations")

// Create indexes for better performance
db.users.createIndex({ "email": 1 }, { unique: true })
db.tours.createIndex({ "category": 1 })
db.tours.createIndex({ "rating": -1 })
db.tours.createIndex({ "tags": 1 })
db.recommendations.createIndex({ "user_id": 1, "date": 1 })
```

## MongoDB Configuration

### For Development:
No authentication required by default. Update `.env`:

```env
DB_CONNECTION=mongodb
DB_HOST=127.0.0.1
DB_PORT=27017
DB_DATABASE=travel_recommendation
DB_USERNAME=
DB_PASSWORD=
```

### For Production:
Enable authentication:

```bash
# Connect to MongoDB
mongosh

# Switch to admin database
use admin

# Create admin user
db.createUser({
  user: "admin",
  pwd: "strongpassword",
  roles: [ { role: "userAdminAnyDatabase", db: "admin" } ]
})

# Create application user
use travel_recommendation
db.createUser({
  user: "travel_app",
  pwd: "apppassword",
  roles: [ { role: "readWrite", db: "travel_recommendation" } ]
})
```

Update `.env`:
```env
DB_CONNECTION=mongodb
DB_HOST=127.0.0.1
DB_PORT=27017
DB_DATABASE=travel_recommendation
DB_USERNAME=travel_app
DB_PASSWORD=apppassword
```

## MongoDB Compass (GUI)

MongoDB Compass is a graphical interface for MongoDB:

1. Download from https://www.mongodb.com/products/compass
2. Connect using connection string:
   ```
   mongodb://localhost:27017/travel_recommendation
   ```
3. Browse collections, run queries, and manage data

## Troubleshooting

### Connection Issues:
```bash
# Check if MongoDB is running
sudo systemctl status mongod

# Check MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log

# Restart MongoDB
sudo systemctl restart mongod
```

### Permission Issues:
```bash
# Fix data directory permissions
sudo chown -R mongodb:mongodb /var/lib/mongodb
sudo chown mongodb:mongodb /tmp/mongodb-27017.sock
```

### Port Already in Use:
```bash
# Check what's using port 27017
sudo lsof -i :27017

# Kill the process
sudo kill -9 <PID>
```

## Performance Tuning

### Indexes for Better Performance:
```javascript
// In MongoDB shell
use travel_recommendation

// Add geospatial index for location-based queries
db.tours.createIndex({ "coordinates": "2dsphere" })

// Add compound index for recommendations
db.recommendations.createIndex({ "user_id": 1, "date": -1 })

// Add text index for search
db.tours.createIndex({ "name": "text", "description": "text" })
```

## Backup and Restore

### Backup:
```bash
mongodump --db travel_recommendation --out /backup/mongodb/
```

### Restore:
```bash
mongorestore --db travel_recommendation /backup/mongodb/travel_recommendation/
```

## Useful MongoDB Commands

```javascript
// Show all databases
show dbs

// Switch database
use travel_recommendation

// Show all collections
show collections

// Count documents
db.tours.count()
db.users.count()

// Find all documents
db.tours.find()

// Find with query
db.tours.find({ category: "adventure" })

// Find one document
db.tours.findOne()

// Delete all documents in collection
db.tours.deleteMany({})

// Drop collection
db.tours.drop()

// Drop database
db.dropDatabase()
```
