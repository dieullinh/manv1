# -*- coding: utf-8 -*-
"""
WSGI Application implementation for Minh An Technology Solutions
Ensures 100% compatibility with Vercel, Gunicorn, uWSGI, Render, Railway, AWS, and Cloud Run.
"""
import json
import os
from dataclasses import asdict

def create_wsgi_app(server_module):
    HTML_PAGE = server_module.HTML_PAGE
    BASE_DIR = server_module.BASE_DIR
    CATALOG_PATH = server_module.CATALOG_PATH
    crm_records = server_module.crm_records
    agent = server_module.agent
    generate_ai_assessment = server_module.generate_ai_assessment
    call_customer_consultant = server_module.call_customer_consultant
    call_gemini_copilot = server_module.call_gemini_copilot
    call_gemini_rewrite_email = server_module.call_gemini_rewrite_email
    user_gemini_api_key = server_module.user_gemini_api_key

    def wsgi_app(environ, start_response):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "/")

        headers = [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
            ("Access-Control-Allow-Headers", "Content-Type"),
        ]

        if method == "OPTIONS":
            start_response("204 No Content", headers)
            return [b""]

        if method == "GET":
            if path in ("/", "/index.html", "/customer", "/business"):
                headers[0] = ("Content-Type", "text/html; charset=utf-8")
                start_response("200 OK", headers)
                return [HTML_PAGE.encode("utf-8")]

            elif path == "/diagram":
                diag_file = os.path.join(BASE_DIR, "workflow_diagram.html")
                if os.path.exists(diag_file):
                    headers[0] = ("Content-Type", "text/html; charset=utf-8")
                    start_response("200 OK", headers)
                    with open(diag_file, "rb") as f:
                        return [f.read()]
                start_response("404 Not Found", headers)
                return [b"Diagram not found"]

            elif path == "/diagram.svg":
                svg_file = os.path.join(BASE_DIR, "workflow_diagram.svg")
                if os.path.exists(svg_file):
                    headers[0] = ("Content-Type", "image/svg+xml; charset=utf-8")
                    start_response("200 OK", headers)
                    with open(svg_file, "rb") as f:
                        return [f.read()]
                start_response("404 Not Found", headers)
                return [b"Diagram SVG not found"]

            elif path == "/api/crm_records":
                start_response("200 OK", headers)
                return [json.dumps(crm_records, ensure_ascii=False).encode("utf-8")]

            elif path == "/api/catalog":
                if os.path.exists(CATALOG_PATH):
                    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                        data = f.read().encode("utf-8")
                else:
                    data = b"[]"
                start_response("200 OK", headers)
                return [data]

            elif path == "/api/export_csv":
                csv_lines = [
                    "Mã Cơ hội,Khách hàng,Người liên hệ,NVKD Phụ trách,Tổng Niêm Yết,Chiết khấu,Thành tiền,Trạng thái Phê duyệt,Thời gian Triển khai,Checkbox Tạo Báo Giá,Link Docs Báo Giá,Nhận định AI"
                ]
                for r in crm_records:
                    warn = r.get("ai_assessment", "").replace('"', '""')
                    csv_lines.append(
                        f'"{r["opp_id"]}","{r["customer_name"]}","{r["contact_person"]}","{r["assigned_rep"]}",'
                        f'{r["subtotal"]},{r["discount_pct"]}%,{r["final_total"]},"{r["approval_status"]}",'
                        f'"{r["lead_time_days"]} ngày",{r.get("checkbox_create_quote", False)},"{r.get("quote_doc_url","")}","{warn}"'
                    )
                csv_data = "\ufeff" + "\n".join(csv_lines)
                headers[0] = ("Content-Type", "text/csv; charset=utf-8")
                headers.append(("Content-Disposition", "attachment; filename=crm_minhan_export.csv"))
                start_response("200 OK", headers)
                return [csv_data.encode("utf-8")]

            else:
                start_response("404 Not Found", headers)
                return [json.dumps({"error": "Not Found"}).encode("utf-8")]

        elif method == "POST":
            try:
                content_length = int(environ.get("CONTENT_LENGTH", 0) or 0)
            except (ValueError, TypeError):
                content_length = 0

            stream = environ.get("wsgi.input")
            body_bytes = stream.read(content_length) if stream and content_length > 0 else b""
            body_str = body_bytes.decode("utf-8", errors="replace") if body_bytes else ""

            try:
                req_data = json.loads(body_str) if body_str else {}
            except Exception:
                req_data = {}

            if path == "/api/customer_chat":
                q = req_data.get("query", "")
                res = call_customer_consultant(q, user_gemini_api_key)
                start_response("200 OK", headers)
                return [json.dumps(res, ensure_ascii=False).encode("utf-8")]

            elif path == "/api/ai_chat":
                q = req_data.get("query", "")
                context = {"records": crm_records}
                reply = call_gemini_copilot(q, context, user_gemini_api_key)
                start_response("200 OK", headers)
                return [json.dumps({"reply": reply}, ensure_ascii=False).encode("utf-8")]

            elif path == "/api/ai_rewrite_email":
                email_txt = req_data.get("email", "")
                tone = req_data.get("tone", "negotiate")
                rewritten = call_gemini_rewrite_email(email_txt, tone, user_gemini_api_key)
                start_response("200 OK", headers)
                return [json.dumps({"rewritten": rewritten}, ensure_ascii=False).encode("utf-8")]

            elif path == "/api/process_inquiry":
                extracted = agent.parse_inquiry_agent(req_data)
                opp = agent.validate_and_price_agent(extracted)
                drafts = agent.generate_proposals_and_drafts(opp)

                status = "Chờ Trưởng phòng duyệt" if opp.approval_required else "Đúng thẩm quyền (<=10%)"
                ai_eval = generate_ai_assessment(opp)

                record = {
                    "opp_id": opp.opportunity_id,
                    "customer_name": opp.customer_name,
                    "contact_person": opp.contact_person,
                    "email": opp.email,
                    "phone": opp.phone,
                    "raw_content": req_data.get("raw_content", ""),
                    "assigned_rep": f"{opp.assigned_rep_name} ({opp.assigned_rep_id})",
                    "rep_email": opp.assigned_rep_email,
                    "subtotal": opp.subtotal,
                    "discount_pct": opp.discount_pct,
                    "discount_amount": opp.discount_amount,
                    "final_total": opp.final_total,
                    "approval_status": status,
                    "lead_time_days": opp.max_lead_time_days,
                    "deadline_feasibility": opp.deadline_feasibility,
                    "ai_assessment": ai_eval,
                    "checkbox_create_quote": False,
                    "quote_doc_url": f"https://docs.google.com/document/d/minhan-{opp.opportunity_id.lower()}-official-quote/edit",
                    "items": [asdict(i) for i in opp.items],
                    "drafts": drafts,
                    "created_at": datetime.now().strftime("%d/%m/%Y %H:%M")
                }
                crm_records.insert(0, record)
                start_response("200 OK", headers)
                return [json.dumps(record, ensure_ascii=False).encode("utf-8")]

            elif path == "/api/manager_decision":
                opp_id = req_data.get("opp_id")
                decision = req_data.get("decision")
                target = next((r for r in crm_records if r["opp_id"] == opp_id), None)
                if target:
                    if decision == "approve":
                        target["approval_status"] = "Đã duyệt (Trưởng phòng duyệt)"
                    elif decision == "reject":
                        target["approval_status"] = "Hoàn tất (Từ chối)"
                        target["checkbox_create_quote"] = False
                    start_response("200 OK", headers)
                    return [json.dumps({"success": True, "record": target}, ensure_ascii=False).encode("utf-8")]
                else:
                    start_response("404 Not Found", headers)
                    return [json.dumps({"error": "Không tìm thấy cơ hội"}, ensure_ascii=False).encode("utf-8")]

            elif path == "/api/trigger_create_quote":
                opp_id = req_data.get("opp_id")
                target = next((r for r in crm_records if r["opp_id"] == opp_id), None)
                if target:
                    target["checkbox_create_quote"] = True
                    doc_url = f"https://docs.google.com/document/d/minhan-{opp_id.lower()}-official-quote/edit"
                    target["quote_doc_url"] = doc_url
                    start_response("200 OK", headers)
                    return [json.dumps({"success": True, "doc_url": doc_url}, ensure_ascii=False).encode("utf-8")]
                else:
                    start_response("404 Not Found", headers)
                    return [json.dumps({"error": "Không tìm thấy cơ hội"}, ensure_ascii=False).encode("utf-8")]

            elif path == "/api/complete_deal":
                opp_id = req_data.get("opp_id")
                target = next((r for r in crm_records if r["opp_id"] == opp_id), None)
                if target:
                    target["approval_status"] = "Chốt đơn / Hoàn tất"
                    start_response("200 OK", headers)
                    return [json.dumps({"success": True, "record": target}, ensure_ascii=False).encode("utf-8")]
                else:
                    start_response("404 Not Found", headers)
                    return [json.dumps({"error": "Không tìm thấy cơ hội"}, ensure_ascii=False).encode("utf-8")]
            else:
                start_response("404 Not Found", headers)
                return [json.dumps({"error": "Endpoint không hợp lệ"}).encode("utf-8")]

        start_response("405 Method Not Allowed", headers)
        return [b"Method Not Allowed"]

    return wsgi_app

