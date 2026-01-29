# Demo Setup & Testing Guide

สำหรับบริษัท Tech AI - คำแนะนำการใช้งาน AI Agent Permission & Audit Layer

---

## 🚀 Quick Start (5 นาที)

### 1. เตรียมข้อมูลทดสอบ

```bash
cd c:\Start-up\ai_agent_mvp
python seed_data.py
```

ผลลัพธ์:
```
🔄 กำลังสร้าง test data...
  ✅ สร้าง Agent: agent-001
  ✅ สร้าง Agent: agent-002
  ✅ สร้าง Agent: agent-003
  ✅ สร้าง Agent: agent-004
  ✅ สร้าง Permission: agent-001 -> read on database
  ... (รวม 11 permissions)

✅ สร้าง test data สำเร็จ!
```

---

### 2. เปิด API

```bash
cd c:\Start-up\ai_agent_mvp
uvicorn main:app --reload
```

เห็น:
```
Uvicorn running on http://127.0.0.1:8000
```

---

### 3. เปิด PowerShell ใหม่ แล้วทดสอบ

```bash
cd c:\Start-up\ai_agent_mvp
```

---

## 🧪 Testing Scenarios

### **Test 1: สำเร็จ - Agent มี Permission**

```bash
curl -X POST http://localhost:8000/agent/request `
  -H "Content-Type: application/json" `
  -d '{"agent_id":"agent-001","action":"read","resource":"database"}'
```

ผลลัพธ์:
```json
{
  "result": "approved",
  "message": "Permission granted for read on database",
  "reason": "all_checks_passed",
  "decision_trace": [
    {"rule_checked": "kill_switch", "rule_result": "passed", "notes": "kill switch off"},
    {"rule_checked": "agent_status", "rule_result": "passed", "notes": "agent active"},
    {"rule_checked": "permission_rule", "rule_result": "passed", "notes": "permission granted"}
  ]
}
```

✅ **ผ่าน** - Agent-001 มี permission read on database

---

### **Test 2: ล้มเหลว - Agent ไม่มี Permission**

```bash
curl -X POST http://localhost:8000/agent/request `
  -H "Content-Type: application/json" `
  -d '{"agent_id":"agent-001","action":"delete","resource":"cache"}'
```

ผลลัพธ์:
```json
{
  "result": "denied",
  "message": "No permission for delete on cache",
  "reason": "permission_rule_failed"
}
```

✅ **ผ่าน** - Correctly blocked

---

### **Test 3: Disabled Agent**

```bash
curl -X POST http://localhost:8000/agent/request `
  -H "Content-Type: application/json" `
  -d '{"agent_id":"agent-004","action":"read","resource":"database"}'
```

ผลลัพธ์:
```json
{
  "result": "denied",
  "message": "Agent agent-004 is disabled",
  "reason": "agent_disabled"
}
```

✅ **ผ่าน** - Correctly blocked disabled agent

---

### **Test 4: ดูล็อก**

```bash
curl http://localhost:8000/logs?agent_id=agent-001
```

ผลลัพธ์: ดูบันทึก actions ทั้งหมดของ agent-001

---

### **Test 5: Kill Switch**

**เปิด kill switch:**
```bash
curl -X POST http://localhost:8000/agent/system-kill-switch `
  -H "Content-Type: application/json" `
  -d '{"enabled":true}'
```

ตอนนี้ all requests จะถูก block:
```bash
curl -X POST http://localhost:8000/agent/request `
  -H "Content-Type: application/json" `
  -d '{"agent_id":"agent-001","action":"read","resource":"database"}'
```

Result:
```json
{
  "result": "denied",
  "reason": "system_kill_switch_enabled",
  "message": "System-wide kill switch is enabled. All agent actions are blocked."
}
```

**ปิด kill switch:**
```bash
curl -X POST http://localhost:8000/agent/system-kill-switch `
  -H "Content-Type: application/json" `
  -d '{"enabled":false}'
```

---

## 🔧 Admin API (สำหรับจัดการ Agents & Permissions)

### **สร้าง Agent ใหม่**

```bash
curl -X POST http://localhost:8000/admin/agents `
  -H "Content-Type: application/json" `
  -d '{
    "id": "agent-005",
    "name": "New Agent",
    "owner": "eve@techcompany.com",
    "status": "active"
  }'
```

---

### **ดูรายการ Agents ทั้งหมด**

```bash
curl http://localhost:8000/admin/agents
```

---

### **สร้าง Permission**

```bash
curl -X POST http://localhost:8000/admin/permissions `
  -H "Content-Type: application/json" `
  -d '{
    "agent_id": "agent-005",
    "action": "write",
    "resource": "database"
  }'
```

---

### **ดูรายการ Permissions**

```bash
curl http://localhost:8000/admin/permissions?agent_id=agent-001
```

---

### **อัปเดต Agent**

```bash
curl -X PUT http://localhost:8000/admin/agents/agent-001 `
  -H "Content-Type: application/json" `
  -d '{"status": "disabled"}'
```

---

### **ลบ Agent**

```bash
curl -X DELETE http://localhost:8000/admin/agents/agent-005
```

---

## 📊 Audit Logs

### **ดูล็อกทั้งหมด**
```bash
curl http://localhost:8000/logs
```

### **ด้วย filter**
```bash
curl "http://localhost:8000/logs?agent_id=agent-001&start_time=2024-01-01T00:00:00&end_time=2024-01-02T00:00:00"
```

---

## ✅ Unit Tests

```bash
pytest tests/ -v
```

ควรเห็น:
```
test_api.py::TestHealthCheck::test_root_endpoint PASSED
test_api.py::TestHealthCheck::test_health_check PASSED
test_api.py::TestAgentPermissions::test_create_agent_and_check_permission PASSED
...
====== 12 passed in 0.50s ======
```

---

## 📚 API Documentation

### **Swagger UI (Interactive)**
```
http://localhost:8000/docs
```

### **ReDoc**
```
http://localhost:8000/redoc
```

---

## 🎯 Key Features to Demo

### 1. **Permission Management**
- ✅ Grant/deny agent actions
- ✅ Check permissions in real-time

### 2. **Kill Switches**
- ✅ Individual agent disable
- ✅ System-wide emergency stop

### 3. **Audit Logging**
- ✅ Complete action trail
- ✅ Query logs by agent/time range

### 4. **Admin API**
- ✅ Create agents
- ✅ Manage permissions
- ✅ Update/delete agents

### 5. **Error Handling**
- ✅ Standardized error responses
- ✅ Clear error messages

### 6. **Rate Limiting**
- ✅ DDoS protection
- ✅ 100 req/min per IP

---

## 📈 Performance Test

Generate load:
```bash
# Run 100 requests
for ($i=1; $i -le 100; $i++) {
  curl -X POST http://localhost:8000/agent/request `
    -H "Content-Type: application/json" `
    -d '{"agent_id":"agent-001","action":"read","resource":"database"}'
}
```

After 100+ requests, you should see:
```
Too many requests
Error: RATE_LIMIT_EXCEEDED
```

✅ Rate limiting is working

---

## 💾 Database

SQLite database location:
```
c:\Start-up\ai_agent_mvp\agent_audit.db
```

Tables:
- `agents` - 4 test agents
- `permissions` - 11 permissions
- `logs` - All action logs
- `system_state` - Kill switch status
- `pending_requests` - Human approvals

---

## 🚨 Troubleshooting

### API not starting?
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill process on port 8000
taskkill /PID <PID> /F
```

### Import errors?
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### seed_data.py fails?
```bash
# Make sure you're in the right directory
cd c:\Start-up\ai_agent_mvp
python seed_data.py
```

---

## 📋 Checklist for Sales Demo

- [ ] Run `python seed_data.py`
- [ ] Start API: `uvicorn main:app --reload`
- [ ] Test permission granted (Test 1)
- [ ] Test permission denied (Test 2)
- [ ] Test disabled agent (Test 3)
- [ ] Test kill switch (Test 5)
- [ ] Show logs (Test 4)
- [ ] Show admin API (create agent)
- [ ] Run tests: `pytest tests/ -v`
- [ ] Show API docs: http://localhost:8000/docs

---

## 🎁 Ready to Ship

✅ All features working
✅ Complete documentation
✅ Unit tests passing
✅ Demo data ready
✅ Admin API functional

**Status: Production Ready** 🚀
