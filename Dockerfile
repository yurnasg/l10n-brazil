FROM odoo:18.0

USER root

# Install packaging and Brazilian base requirements
RUN pip install --no-cache-dir --break-system-packages \
    packaging \
    num2words \
    erpbrasil.base \
    phonenumbers \
    email-validator \
    openupgradelib \
    odoo-addon-hr-employee-relative

USER odoo
