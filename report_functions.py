def generate_report(self):
    selected_product_name = self.product_combobox.get()
    if not selected_product_name:
        messagebox.showerror("Błąd", "Proszę wybrać produkt!")
        return

    product = session.query(Product).filter_by(product_name=selected_product_name).first()
    if not product:
        messagebox.showerror("Błąd", "Nie znaleziono produktu!")
        return

    report_window = tk.Toplevel(self)
    report_window.title("Raport")

    report_text = tk.Text(report_window, wrap="word", width=50, height=50)
    report_text.pack(padx=10, pady=10)

    report_content = f"Raport dla produktu: {product.product_name}\n\n"
    report_content += "Surowce i ich ceny: \n"

    for resource, ilosc in session.query(Resource, product_resource_table.c.ilosc).filter(
            product_resource_table.c.product_id == product.id).filter(
            product_resource_table.c.resource_id == Resource.id):
        report_content += f"{resource.resource_name} - {resource.resource_price} PLN (Ilość: {ilosc})\n"

    report_text.insert("1.0", report_content)
    report_text.config(state="disabled")

    save_button = ttk.Button(report_window, text="Zapisz jako PDF",
                             command=lambda: self.save_report_as_pdf(report_content))
    save_button.pack(pady=10)


# def save_report_as_pdf(self, report_text, save_path):
#     pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
#     c = canvas.Canvas(save_path, pagesize=letter)
#     c.setFont('DejaVuSans', 12)

#     lines = report_text.split('\n')
#     y = 750
#     for line in lines:
#         c.drawString(50, y, line)
#         y -= 20
#         if y < 50:
#             c.showPage()
#             c.setFont('DejaVuSans', 12)
#             y = 750

#     c.save()
def save_report_as_pdf(self, report_content):
    file_path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                             filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")])
    if file_path:
        try:
            pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
            c = canvas.Canvas(file_path, pagesize=letter)
            c.setFont('DejaVuSans', 12)
            width, height = letter
            c.drawString(100, height - 100, "Raport")
            text = c.beginText(100, height - 120)
            text.setFont("DejaVuSans", 12)
            for line in report_content.split('\n'):
                text.textLine(line)
            c.drawText(text)
            c.showPage()
            c.save()
            messagebox.showinfo("Sukces", "Raport zapisany pomyślnie jako PDF")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać raportu: {str(e)}")