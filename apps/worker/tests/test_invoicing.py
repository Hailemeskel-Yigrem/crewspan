from worker.jobs.invoicing import generate_from_work_order


def test_generate_invoice():
    result = generate_from_work_order("wo-123", tenant_id="t-1")
    assert result["invoice_number"].startswith("INV-")
