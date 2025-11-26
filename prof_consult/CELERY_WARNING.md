# ⚠️ IMPORTANT: DO NOT CREATE celery.py IN THIS DIRECTORY

**The Celery configuration is located at:** `prof_consult/celery.py`

**DO NOT** create a `celery.py` file in this directory (`prof_consult/`) as it will cause an import conflict with the Celery library.

## Why?

When Python tries to import `from celery import Celery`, it first looks in the current directory. If there's a `celery.py` file here, Python will try to import from it instead of the actual Celery library, causing an `ImportError`.

## The Correct Structure

```
prof_consult/
├── celery.py ❌ NEVER CREATE THIS FILE HERE
├── prof_consult/
│   ├── __init__.py
│   ├── celery.py ✅ CORRECT LOCATION
│   ├── settings.py
│   └── ...
└── manage.py
```

## If You See This Error

```
ImportError: cannot import name 'Celery' from 'celery'
```

**Solution:** Delete `prof_consult/celery.py` (this directory level)
```bash
rm prof_consult/celery.py
```

The correct Celery app is already configured in `prof_consult/prof_consult/celery.py` ✅
