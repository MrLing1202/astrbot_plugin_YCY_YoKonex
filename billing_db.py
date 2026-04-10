import os
import json
import time
import hashlib
from typing import Dict, List, Optional, Any


class BillingDB:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.quota_db_path = os.path.join(data_dir, "quota_db.json")
        self.redeem_db_path = os.path.join(data_dir, "redeem_db.json")
        self._ensure_data_dir()
        self.quota_db = self._load_quota_db()
        self.redeem_db = self._load_redeem_db()

    def _ensure_data_dir(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _load_quota_db(self) -> Dict[str, Any]:
        if os.path.exists(self.quota_db_path):
            try:
                with open(self.quota_db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _load_redeem_db(self) -> Dict[str, Any]:
        if os.path.exists(self.redeem_db_path):
            try:
                with open(self.redeem_db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_quota_db(self):
        with open(self.quota_db_path, "w", encoding="utf-8") as f:
            json.dump(self.quota_db, f, ensure_ascii=False, indent=2)

    def _save_redeem_db(self):
        with open(self.redeem_db_path, "w", encoding="utf-8") as f:
            json.dump(self.redeem_db, f, ensure_ascii=False, indent=2)

    def get_user_quota(self, user_id: str) -> Dict[str, Any]:
        if user_id not in self.quota_db:
            return {
                "free_quota": 0,
                "paid_quota": 0,
                "last_refresh_ts": 0
            }
        return self.quota_db[user_id]

    def update_user_quota(self, user_id: str, free_quota: Optional[int] = None, 
                          paid_quota: Optional[int] = None, 
                          last_refresh_ts: Optional[int] = None):
        if user_id not in self.quota_db:
            self.quota_db[user_id] = {
                "free_quota": 0,
                "paid_quota": 0,
                "last_refresh_ts": 0
            }
        
        if free_quota is not None:
            self.quota_db[user_id]["free_quota"] = free_quota
        if paid_quota is not None:
            self.quota_db[user_id]["paid_quota"] = paid_quota
        if last_refresh_ts is not None:
            self.quota_db[user_id]["last_refresh_ts"] = last_refresh_ts
        
        self._save_quota_db()

    def consume_quota(self, user_id: str, amount: int) -> bool:
        quota = self.get_user_quota(user_id)
        total = quota["free_quota"] + quota["paid_quota"]
        
        if total < amount:
            return False
        
        if quota["free_quota"] >= amount:
            self.update_user_quota(user_id, free_quota=quota["free_quota"] - amount)
        else:
            remaining = amount - quota["free_quota"]
            self.update_user_quota(
                user_id, 
                free_quota=0, 
                paid_quota=quota["paid_quota"] - remaining
            )
        
        return True

    def is_order_redeemed(self, order_id: str) -> bool:
        return order_id in self.redeem_db

    def redeem_order(self, order_id: str, user_id: str, amount: int):
        self.redeem_db[order_id] = {
            "user_id": user_id,
            "amount": amount,
            "ts": int(time.time())
        }
        self._save_redeem_db()

    def get_all_quota_records(self, limit: int = 50) -> List[Dict[str, Any]]:
        records = []
        for user_id, data in self.quota_db.items():
            records.append({
                "user_id": user_id,
                **data
            })
        return sorted(records, key=lambda x: x.get("last_refresh_ts", 0), reverse=True)[:limit]

    def get_all_redeem_records(self, user_id: Optional[str] = None, 
                                order_id: Optional[str] = None, 
                                limit: int = 50) -> List[Dict[str, Any]]:
        records = []
        for oid, data in self.redeem_db.items():
            if order_id and oid != order_id:
                continue
            if user_id and data.get("user_id") != user_id:
                continue
            records.append({
                "order_id": oid,
                **data
            })
        return sorted(records, key=lambda x: x.get("ts", 0), reverse=True)[:limit]
