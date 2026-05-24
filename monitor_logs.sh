#!/bin/bash

echo "=== Food Analyzer Log Monitor ==="
echo "1. API Logs"
echo "2. Traces"
echo "3. Nginx Logs"
echo "4. Database Logs"
echo "5. All Logs"
echo "6. Recent Errors"
echo "================================"
read -p "Choose option: " option

case $option in
  1)
    docker-compose logs -f api1 api2 api3
    ;;
  2)
    tail -f logs/traces.log
    ;;
  3)
    docker-compose logs -f nginx
    ;;
  4)
    docker-compose logs -f postgres
    ;;
  5)
    docker-compose logs -f
    ;;
  6)
    echo "Recent errors:"
    grep -r "ERROR\|Exception" logs/ | tail -20
    ;;
esac
