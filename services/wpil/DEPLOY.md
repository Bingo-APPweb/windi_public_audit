# WPIL Deployment Instructions

## 1. Install systemd service

```bash
sudo cp /opt/windi/services/wpil/wpil.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable wpil
sudo systemctl start wpil
```

## 2. Verify service status

```bash
sudo systemctl status wpil
```

## 3. Check logs

```bash
journalctl -u wpil -f
```

## 4. Test endpoints

```bash
# Health check
curl http://localhost:8146/health

# Verify endpoint
curl -X POST http://localhost:8146/verify \
  -H "Content-Type: application/json" \
  -d '{"receipt": {...}}'
```

## 5. Configure nginx

Add to `/etc/nginx/sites-available/default`:

```nginx
location /wpil/ {
    proxy_pass http://localhost:8146/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Then reload nginx:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

## 6. Test external access

```bash
curl https://windi-domain.com/wpil/health
```

## Service Info

- **Port:** 8146
- **Path:** /opt/windi/services/wpil
- **User:** windi
- **Logs:** `journalctl -u wpil`
