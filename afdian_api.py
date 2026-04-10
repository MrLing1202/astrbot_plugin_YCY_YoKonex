import requests
import hashlib
import time
from typing import Dict, Optional, Any


class AfdianAPI:
    def __init__(self, base_url: str, user_id: str, token: str):
        self.base_url = base_url
        self.user_id = user_id
        self.token = token

    def _generate_sign(self, params: Dict[str, Any]) -> str:
        sorted_params = sorted(params.items())
        param_str = "&".join([f"{k}={v}" for k, v in sorted_params])
        sign_str = f"{self.token}{param_str}"
        return hashlib.md5(sign_str.encode("utf-8")).hexdigest()

    def query_order(self, out_trade_no: Optional[str] = None, 
                    page: int = 1, page_size: int = 10) -> Optional[Dict[str, Any]]:
        params = {
            "user_id": self.user_id,
            "ts": int(time.time()),
            "page": page,
            "page_size": page_size
        }
        
        if out_trade_no:
            params["out_trade_no"] = out_trade_no

        params["sign"] = self._generate_sign(params)

        try:
            response = requests.post(
                f"{self.base_url}/api/open/query-order",
                json=params,
                timeout=10
            )
            result = response.json()
            
            if result.get("ec") == 200:
                return result.get("data")
            else:
                print(f"爱发电 API 错误: {result.get('em')}")
                return None
        except Exception as e:
            print(f"爱发电 API 请求失败: {e}")
            return None

    def get_order_by_id(self, out_trade_no: str) -> Optional[Dict[str, Any]]:
        data = self.query_order(out_trade_no=out_trade_no, page_size=1)
        if data and "list" in data and len(data["list"]) > 0:
            return data["list"][0]
        return None
