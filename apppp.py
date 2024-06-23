import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox, filedialog
from sqlalchemy import create_engine, Column, Integer, String, Float, Table, ForeignKey, select, update
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, joinedload
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


user = "root"
password = "P2wcio27"
# Konfiguracja bazy danych
DATABASE_URL = f"mysql+pymysql://{user}:{password}@localhost:3306/production"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

# Tabela relacyjna
product_resource_table = Table(
    'product_resource', Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id'), primary_key=True),
    Column('resource_id', Integer, ForeignKey('resources.id'), primary_key=True),
    Column('resource_name', String, nullable=False),
    Column('ilosc', Float, nullable=False)
)

class Resource(Base):
    __tablename__ = 'resources'
    id = Column(Integer, primary_key=True)
    resource_name = Column(String(50), unique=True, nullable=False)
    resource_price = Column(Float, nullable=False)

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    product_name = Column(String(50), unique=True, nullable=False)
    retail_price = Column(Float, nullable=False)
    wholesale_price = Column(Float, nullable=False)
    last_cost_of_production = Column(Float, nullable=False)
    resources = relationship('Resource', secondary=product_resource_table, backref='products')

class ResourcePriceHistory(Base):
    __tablename__ = 'resource_price_history'
    id = Column(Integer, primary_key=True)
    resource_name = Column(String)
    resource_id = Column(Integer)
    resource_price = Column(Float)
    change_date = Column(String)

class ProductCostProductionHistory(Base):
    __tablename__ = 'product_cost_production_history'
    id = Column(Integer, primary_key=True)
    product_name = Column(String)
    product_id = Column(Integer)
    cost_of_production = Column(Float)
    change_date = Column(String)

class FixedCost(Base):
    __tablename__ = 'fixed_costs'
    id = Column(Integer, primary_key=True)
    name_of_fixed_cost = Column(String(255), nullable=False)
    cost = Column(Float, nullable=False)

Base.metadata.create_all(engine)

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Aplikacja do zarządzania produktami i surowcami")

        tabControl = ttk.Notebook(self)
        self.tab1 = ttk.Frame(tabControl)
        self.tab2 = ttk.Frame(tabControl)
        self.tab3 = ttk.Frame(tabControl)
        self.tab4 = ttk.Frame(tabControl)
        self.tab5 = ttk.Frame(tabControl)

        tabControl.add(self.tab1, text="Aktualizacja cen surowców")
        tabControl.add(self.tab2, text="Koszt jednostkowy produktu")
        tabControl.add(self.tab3, text="Przypisywanie surowców do produktu")
        tabControl.add(self.tab4, text="Dodawanie surowców do bazy")
        tabControl.add(self.tab5, text="Edycja kosztów stałych")
        tabControl.pack(expand=1, fill="both")

        self.create_tab1()
        self.create_tab2()
        self.create_tab3()
        self.create_tab4()
        self.create_tab5()

    def create_tab1(self):

        self.tab1.grid_columnconfigure(tuple(range(200)), weight=1)
        self.tab1.grid_rowconfigure(tuple(range(200)), weight=1)

        self.label1 = ttk.Label(self.tab1, text="Nazwa surowca:")
        self.label1.grid(column=0, row=0, padx=10, pady=10)

        self.resource_combobox = ttk.Combobox(self.tab1)
        self.resource_combobox.grid(column=0, row=1, padx=10, pady=10)
        self.resource_combobox.bind("<<ComboboxSelected>>", self.display_current_resource_price_and_treeview)
        #self.resource_combobox.bind("<<ComboboxSelected>>", self.sort_column, add=True )
        self.load_surowce(self.resource_combobox)



        self.label2 = ttk.Label(self.tab1, text="Nowa cena:")
        self.label2.grid(column=1, row=0, padx=10, pady=10)

        self.cena_entry = ttk.Entry(self.tab1)
        self.cena_entry.grid(column=1, row=1, columnspan=1, padx=10, pady=10)

        self.current_price_label = ttk.Label(self.tab1, text="Aktualna cena: ")
        self.current_price_label.grid(column=0, row=2, padx=10, pady=10)

        self.update_button = ttk.Button(self.tab1, text="Aktualizuj cenę", command=self.update_price)
        self.update_button.grid(column=1, row=3, columnspan=2, padx=10, pady=10)

        self.filter_button = ttk.Button(self.tab1, text="Filtrowanie ▼", command=self.toggle_filter_window)
        self.filter_button.grid(column=0, row=3, columnspan=2, padx=10, pady=10)

        self.filter_window = tk.Toplevel(self)
        self.filter_window.title("Filtrowanie")
        self.filter_window.withdraw()  # Ukryj okno na początku
        self.filter_window.protocol("WM_DELETE_WINDOW", self.hide_filter_window)  # Obsługa zamknięcia okna


        #self.filter_frame = ttk.Frame(self.tab1)
        self.filter_frame = ttk.Frame(self.filter_window)
        self.filter_frame.grid(column=1, row=4, columnspan=2, padx=10, pady=10)
        self.filter_frame.grid_remove()

        self.filter_vars = {}
        resources = session.query(Resource).all()
        for resource in resources:
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(self.filter_window, text=resource.resource_name, variable=var)
            chk.pack(anchor='w')
            self.filter_vars[resource.resource_name] = var

        self.apply_filter_button = ttk.Button(self.filter_window, text="Zastosuj filtr", command=self.apply_filter)
        self.apply_filter_button.pack(pady=5)



        self.history_tree = ttk.Treeview(self.tab1, columns=("resource_id", "resource_name", "resource_price", "change_date"),
                                         show="headings")
        self.history_tree.heading("resource_id", text="ID surowca", anchor=tk.CENTER)
        self.history_tree.heading("resource_name", text= "Nazwa surowca", anchor=tk.CENTER)
        self.history_tree.heading("resource_price", text="Cena", anchor=tk.CENTER)
        self.history_tree.heading("change_date", text="Data zmiany", anchor=tk.CENTER)
        self.history_tree.column("resource_id", anchor=tk.CENTER)
        self.history_tree.column("resource_name", anchor=tk.CENTER)
        self.history_tree.column("resource_price", anchor=tk.CENTER)
        self.history_tree.column("change_date", anchor=tk.CENTER)
        self.history_tree.bind("<Button-1>", self.sort_column)
        self.history_tree.grid(column=0, row=5, columnspan=2, padx=10, pady=10)

        self.load_price_history()

    #def apply_filters(self):
    #    self.selected_resources.clear()
    #    for resource_name, var in self.resource_filters.items():
    #        if var.get() == 1:
    #            self.selected_resources.add(resource_name)
#
    #    self.filter_data()
#
    #def filter_data(self):
    #    # Wczytaj dane z bazy danych z uwzględnieniem wybranych filtrów
    #    session = Session()
    #    query = session.query(Resource).filter(Resource.resource_name.in_(self.selected_resources)).all()
    #    session.close()

    def toggle_filter_frame(self):
        if self.filter_frame.winfo_viewable():
            self.filter_frame.grid_remove()
        else:
            self.filter_frame.grid()

    def toggle_filter_window(self):
        if self.filter_window.state() == "withdrawn":
            self.filter_window.deiconify()  # Pokaż okno
        else:
            self.filter_window.withdraw()  # Ukryj okno

    def hide_filter_window(self):
        self.filter_window.withdraw()  # Ukryj okno


    def apply_filter(self):
        self.history_tree.delete(*self.history_tree.get_children())
        selected_resources = [name for name, var in self.filter_vars.items() if var.get()]
        if selected_resources:
            filtered_history = session.query(ResourcePriceHistory).filter(
                ResourcePriceHistory.resource_name.in_(selected_resources)).order_by(ResourcePriceHistory.change_date.desc()).all()
        else:
            filtered_history = session.query(ResourcePriceHistory).order_by(
                ResourcePriceHistory.change_date.desc()).all()

        for entry in filtered_history:
            self.history_tree.insert("", "end",
                                     values=(entry.resource_id, entry.resource_name, entry.resource_price,
                                             entry.change_date))
        self.hide_filter_window()
    def display_current_resource_price_and_treeview(self, event):

        self.resource_name = event.widget.get()
        stmt = select(Resource).where(Resource.resource_name == f'{self.resource_name}')
        result = session.execute(stmt)
        for resource_obj in result.scalars():
            self.current_price_label.config(text=f'Aktualna cena: {resource_obj.resource_price}')
            #print(resource_obj)

        #self.resource_name = event.widget.get()
        price_history_filtred = session.query(ResourcePriceHistory).filter(
            ResourcePriceHistory.resource_name == f'{self.resource_name}').order_by(ResourcePriceHistory.change_date.desc())
        self.history_tree.delete(*self.history_tree.get_children())
        for entry in price_history_filtred:
            self.history_tree.insert("", "end",
                                     values=(
                                         entry.resource_id, entry.resource_name, entry.resource_price,
                                         entry.change_date))

    #def add_record_to_cost_production_table(self):



       # self.resource_name = event.widget.get()
       # #print(self.resource_name)
       # filtered_history = select(ResourcePriceHistory).filter(ResourcePriceHistory.resource_name == self.resource_name)
       # result = session.execute(filtered_history)
       # #print(result)
       # for entry in result.scalars():
#
       #     self.history_tree.insert("", "end",
       #                              values=(entry.resource_id, entry.resource_name, entry.resource_price,
       #                                      entry.change_date))

        #self.refresh_resource_update_treeview()

    def update_price(self):


        try:
            new_price = float(self.cena_entry.get())
            resource = session.query(Resource).filter_by(resource_name=self.resource_name).first()
            if resource.resource_price == new_price:
                messagebox.showinfo("BŁĄD", "Podano taką samą cenę!")
            elif resource:
                    resource.resource_price = new_price
                    session.commit()
                    messagebox.showinfo("Sukces", "Cena surowca została zaktualizowana!")
                    change_entry = ResourcePriceHistory(
                        resource_id=resource.id,
                        resource_name=resource.resource_name,
                        resource_price=resource.resource_price,
                        change_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    )
                    session.add(change_entry)
                    session.commit()
            else:
                    messagebox.showinfo("Sukces", "Cena surowca zaktualizowana")
            session.close()
        except ValueError:
            messagebox.showerror("Błąd", "Proszę podać prawidłową cenę")
        self.refresh_resource_update_treeview()


    def create_tab2(self):
        self.label3 = ttk.Label(self.tab2, text="Nazwa produktu:")
        self.label3.grid(column=0, row=0, columnspan=2, padx=10, pady=10)

        self.product_combobox = ttk.Combobox(self.tab2)
        self.product_combobox.grid(column=1, row=0, padx=10, pady=10)
        self.load_products(self.product_combobox)
        self.product_combobox.bind("<<ComboboxSelected>>", self.display_product_cost_history)

        self.cost_button = ttk.Button(self.tab2, text="Oblicz koszt", command=self.calculate_cost)
        self.cost_button.grid(column=0, row=1, columnspan=2, padx=10, pady=10)

        self.report_buttron = ttk.Button(self.tab2, text="Generuj raport!", command=self.generate_report)
        self.report_buttron.grid(column=0, row=1, padx=10, pady=10)

        self.result_label = ttk.Label(self.tab2, text="")
        self.result_label.grid(column=0, row=2, columnspan=2, padx=10, pady=10)

        self.product_cost_tree = ttk.Treeview(self.tab2,
                                         columns=("product_id", "product_name", "cost_of_production", "change_date"),
                                         show="headings")
        self.product_cost_tree.heading("product_id", text="ID produtku", anchor=tk.CENTER)
        self.product_cost_tree.heading("product_name", text="Nazwa surowca", anchor=tk.CENTER)
        self.product_cost_tree.heading("cost_of_production", text="Cena", anchor=tk.CENTER)
        self.product_cost_tree.heading("change_date", text="Data zmiany", anchor=tk.CENTER)
        self.product_cost_tree.column("product_id", anchor=tk.CENTER)
        self.product_cost_tree.column("product_name", anchor=tk.CENTER)
        self.product_cost_tree.column("cost_of_production", anchor=tk.CENTER)
        self.product_cost_tree.column("change_date", anchor=tk.CENTER)
        self.product_cost_tree.bind("<Button-1>")
        self.product_cost_tree.grid(column=0, row=5, columnspan=2, padx=10, pady=10)

    def display_product_cost_history(self, event):
        self.product_name = self.product_combobox.get()
        self.refresh_product_cost_treeview()


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

        for resource, ilosc in session.query(Resource, product_resource_table.c.ilosc).filter(product_resource_table.c.product_id == product.id).filter(product_resource_table.c.resource_id == Resource.id):
            report_content += f"{resource.resource_name} - {resource.resource_price} PLN (Ilość: {ilosc})\n"

        report_text.insert("1.0", report_content)
        report_text.config(state="disabled")

        save_button = ttk.Button(report_window, text="Zapisz jako PDF", command=lambda: self.save_report_as_pdf(report_content))
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




    def refresh_product_cost_treeview(self):
        self.product_cost_tree.delete(*self.product_cost_tree.get_children())
        self.load_product_cost_history()

    def load_product_cost_history(self):
        selected_product = self.product_combobox.get()
        #print(selected_product)
        if selected_product:
            cost_history = session.query(ProductCostProductionHistory).filter_by(
                product_name=selected_product).order_by(ProductCostProductionHistory.change_date.desc()).all()
            for entry in cost_history:
                self.product_cost_tree.insert("", "end",
                                              values=(entry.product_id, entry.product_name, entry.cost_of_production,
                                                      entry.change_date))
    def calculate_cost(self):
        product_name = self.product_combobox.get()
        product = session.query(Product).filter_by(product_name=product_name).first()
        if product:
            cost = sum([
                resource.resource_price * ilosc
                for resource, ilosc in session.query(Resource, product_resource_table.c.ilosc)
                .filter(product_resource_table.c.product_id == product.id)
                .filter(product_resource_table.c.resource_id == Resource.id)
            ])
            self.result_label.config(text=f"Koszt jednostkowy produktu: {cost:.2f}")
            product = session.query(Product).filter_by(product_name=self.product_name).first()
            change_entry = ProductCostProductionHistory(
                product_id=product.id,
                product_name=product.product_name,
                cost_of_production=cost,
                change_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            session.add(change_entry)
            session.commit()
            self.refresh_product_cost_treeview()
        else:
            self.result_label.config(text="Produkt nie znaleziony")

    def create_tab3(self):
        self.label4 = ttk.Label(self.tab3, text="Nazwa produktu:")
        self.label4.grid(column=0, row=0, padx=10, pady=10)

        self.product_combobox_tab3 = ttk.Combobox(self.tab3)
        self.product_combobox_tab3.grid(column=1, row=0, padx=10, pady=10)
        self.load_products(self.product_combobox_tab3)
        self.product_combobox_tab3.bind("<<ComboboxSelected>>", self.display_product_resources)

        self.resources_tree = ttk.Treeview(self.tab3, columns=("resource_id", "resource_name", "resource_quantity"),
                                           show="headings")
        self.resources_tree.heading("resource_id", text="ID surowca", anchor=tk.CENTER)
        self.resources_tree.heading("resource_name", text="Nazwa surowca", anchor=tk.CENTER)
        self.resources_tree.heading("resource_quantity", text="Ilość", anchor=tk.CENTER)
        self.resources_tree.column("resource_id", anchor=tk.CENTER)
        self.resources_tree.column("resource_name", anchor=tk.CENTER)
        self.resources_tree.column("resource_quantity", anchor=tk.CENTER)
        self.resources_tree.grid(column=0, row=5, columnspan=2, padx=10, pady=10)

        self.label5 = ttk.Label(self.tab3, text="Nazwa surowca:")
        self.label5.grid(column=0, row=1, padx=10, pady=10)

        self.resource_combobox_tab3 = ttk.Combobox(self.tab3)
        self.resource_combobox_tab3.grid(column=1, row=1, padx=10, pady=10)
        self.load_surowce(self.resource_combobox_tab3)

        self.label6 = ttk.Label(self.tab3, text="Ilość surowca:")
        self.label6.grid(column=0, row=2, padx=10, pady=10)

        self.ilosc_entry = ttk.Entry(self.tab3)
        self.ilosc_entry.grid(column=1, row=2, padx=10, pady=10)

        self.add_resource_button = ttk.Button(self.tab3, text="Dodaj surowiec", command=self.add_resource_to_product)
        self.add_resource_button.grid(column=0, row=3, columnspan=2, padx=10, pady=10)

        #self.save_product_button = ttk.Button(self.tab3, text="Zapisz produkt", command=self.save_product)
        #self.save_product_button.grid(column=0, row=4, columnspan=2, padx=10, pady=10)

        self.product_resource = []

    def display_product_resources(self, event):
        self.refresh_resources_treeview()

    def refresh_resources_treeview(self):
        self.resources_tree.delete(*self.resources_tree.get_children())
        self.load_product_resources()


    def load_product_resources(self):
        selected_product_name = self.product_combobox_tab3.get()
        if selected_product_name:
            product = session.query(Product).filter_by(product_name=selected_product_name).first()
            if product:
                resources = session.query(product_resource_table).filter_by(product_id= product.id)
                #print(product.id)
                for entry in resources:
                    resource = session.query(product_resource_table).filter_by(resource_id=entry.resource_id).first()
                    #print(entry)
                    #print(resource)
                    self.resources_tree.insert("", "end",
                                               values=(
                                               entry.resource_id, entry.resource_name, entry.ilosc))

    def create_tab4(self):
        self.label7 = ttk.Label(self.tab4, text="Nazwa surowca:")
        self.label7.grid(column=0, row=0, padx=10, pady=10)

        self.new_resource_entry = ttk.Entry(self.tab4)
        self.new_resource_entry.grid(column=1, row=0, padx=10, pady=10)

        self.label8 = ttk.Label(self.tab4, text="Cena surowca:")
        self.label8.grid(column=0, row=1, padx=10, pady=10)

        self.new_cena_entry = ttk.Entry(self.tab4)
        self.new_cena_entry.grid(column=1, row=1, padx=10, pady=10)

        self.add_resource_button = ttk.Button(self.tab4, text="Dodaj surowiec", command=self.add_new_resource)
        self.add_resource_button.grid(column=0, row=2, columnspan=2, padx=10, pady=10)

    def add_new_resource(self):
        resource_name = self.new_resource_entry.get()
        try:
            resource_price = float(self.new_cena_entry.get())
            new_resource = Resource(resource_name=resource_name, resource_price=resource_price)
            session.add(new_resource)
            session.commit()
            messagebox.showinfo("Sukces", "Surowiec dodany pomyślnie")
            self.load_surowce(self.resource_combobox)  # Aktualizacja listy surowców
            self.load_surowce(self.resource_combobox_tab3)
        except ValueError:
            messagebox.showerror("Błąd", "Proszę podać prawidłową cenę")

    def load_products(self, combobox):
        products = session.query(Product).all()
        product_names = [product.product_name for product in products]
        combobox['values'] = product_names

    def load_surowce(self, combobox):
        resources = session.query(Resource).all()
        resource_names = [resource.resource_name for resource in resources]
       ##### self.resource_####
        combobox['values'] = resource_names


    def add_resource_to_product(self):
        selected_product_name = self.product_combobox_tab3.get()
        selected_resource_name = self.resource_combobox_tab3.get()
        try:
            ilosc = float(self.ilosc_entry.get())
            product = session.query(Product).filter_by(product_name=selected_product_name).first()
            resource = session.query(Resource).filter_by(resource_name=selected_resource_name).first()
            if product and resource:
                stmt = select(product_resource_table).where(
                    product_resource_table.c.product_id == product.id,
                    product_resource_table.c.resource_id == resource.id
                )
                existing_entry = session.execute(stmt).fetchone()
                if existing_entry:
                    existing_ilosc = existing_entry[3]
                    new_ilosc = existing_ilosc + ilosc

                    stmt_update = (
                        update(product_resource_table)
                        .where(product_resource_table.c.product_id == product.id)
                        .where(product_resource_table.c.resource_id == resource.id)
                        .values(ilosc=new_ilosc)
                    )
                    session.execute(stmt_update)
                    session.commit()
                    messagebox.showinfo("Sukces",
                                        f"Zaktualizowano ilość surowca: {resource.resource_name} do: {new_ilosc}")
                else:
                    session.execute(product_resource_table.insert().values(
                        product_id=product.id,
                        resource_id=resource.id,
                        resource_name=resource.resource_name,
                        ilosc=ilosc
                    ))
                    session.commit()
                    messagebox.showinfo("Sukces", f"Dodano surowiec: {resource.resource_name} w ilości: {ilosc}")
            else:
                messagebox.showerror("Błąd", "Nie znaleziono produktu lub surowca")
        except ValueError:
            messagebox.showerror("Błąd", "Proszę podać prawidłową ilość")

    def load_price_history(self):
        session = Session()
        #resource_name = name
        #print(resource_name)
        if self.resource_combobox.get() == "":
            price_history = session.query(ResourcePriceHistory).order_by(ResourcePriceHistory.change_date.desc()).all()

         #   price_history = session.query(ProductCostProductionHistory).order_by(ProductCostProductionHistory.change_date.desc()).all()
        #else:
        #    price_history = self.display_current_resource_price_and_treeview

        for entry in price_history:
            self.history_tree.insert("", "end",
                        values=(entry.resource_id, entry.resource_name, entry.resource_price, entry.change_date))
        session.close()

    def save_product(self):
        selected_product_name = self.product_combobox_tab3.get()
        product = session.query(Product).filter_by(product_name=selected_product_name).first()
        if not product:
            product = Product(product_name=selected_product_name)
            session.add(product)
            session.commit()
            product = session.query(Product).filter_by(product_name=selected_product_name).first()

        for resource_name, resource_id, ilosc in self.product_resource:
            stmt = select(product_resource_table).where(
                product_resource_table.c.product_id == product.id,
                product_resource_table.c.resource_id == resource_id
            )
            existing_entry = session.execute(stmt).fetchone()
            if existing_entry:
                session.execute(product_resource_table.update().where(
                    product_resource_table.c.product_id == product.id,
                    product_resource_table.c.resource_id == resource_id
                ).values(ilosc=ilosc))
            else:
                session.execute(product_resource_table.insert().values(
                    product_id=product.id,
                    resource_id=resource_id,
                    resource_name=resource_name,
                    ilosc=ilosc
                ))
        session.commit()
        self.product_resource = []
        messagebox.showinfo("Sukces", "Produkt zapisany pomyślnie")

    def refresh_resource_update_treeview(self):
        self.history_tree.delete(*self.history_tree.get_children())
        self.load_price_history()

    def sort_column(self, event):
        column = self.history_tree.identify_column(event.x)
        column_index = int(column[1:]) - 1
        column_name = self.history_tree["columns"][column_index]
        current_order = self.history_tree.heading(column_name, "text")

        if event.widget.identify_region(event.x, event.y) == "cell":
            print(f"Kliknięto na wartość w kolumnie {column_name}, sortowanie zostanie zablokowane")
            return

        if "▲" in current_order:
            self.history_tree.heading(column_name, text=current_order.replace(" ▲", " ▼"))
            order = False
        elif "▼" in current_order:
            self.history_tree.heading(column_name, text=current_order.replace(" ▼", ""))
            order = None
        else:
            self.history_tree.heading(column_name, text=current_order + " ▲")
            order = True

        data = [(self.history_tree.set(child, column_name), child) for child in self.history_tree.get_children("")]
        if order is not None:
            data.sort(reverse=order)
            for index, (val, item) in enumerate(data):
                self.history_tree.move(item, "", index)
        else:
            self.history_tree.delete(*self.history_tree.get_children())
            self.load_price_history()


    def create_tab5(self):

        self.tab5.grid_columnconfigure(tuple(range(200)), weight=1)
        self.tab5.grid_rowconfigure(tuple(range(200)), weight=1)

        self.label9 = ttk.Label(self.tab5, text="Nazwa kosztu stałego: ")
        self.label9.grid(column=0, row=0, padx=0, pady=0)

        self.new_fixed_cost_entry = ttk.Entry(self.tab5)
        self.new_fixed_cost_entry.grid(column=1, row=0, padx=10, pady=10)

        self.label10 = ttk.Label(self.tab5, text="Koszt: ")
        self.label10.grid(column=0, row=1, padx=10, pady=10)

        self.new_fixed_cost_cost = ttk.Entry(self.tab5)
        self.new_fixed_cost_cost.grid(column=1, row=1, padx=10, pady=10)

        self.add_fixed_cost_button = ttk.Button(self.tab5, text="Dodaj koszt stały")
        self.add_fixed_cost_button.grid(column=1, row=2, padx=10, pady=10)

    def add_fixed_cost(self):
        name = self.entry_name.get()
        try:
            cost = float(self.entry_cost.get())
            new_cost = FixedCost(name=name, cost=cost)
            session.add(new_cost)
            session.commit()
            messagebox.showinfo("Sukces", f"Dodano koszt: {name} ({cost:.2f})")
            self.load_fixed_costs()
        except ValueError:
            messagebox.showerror("Błąd", "Proszę podać prawidłową kwotę kosztu")

    def update_fixed_cost(self):
        selected_item = self.fixed_costs_tree.focus()
        if selected_item:
            item_values = self.fixed_costs_tree.item(selected_item, "values")
            cost_id = int(selected_item.lstrip("I"))
            name = self.entry_name.get()
            try:
                cost = float(self.entry_cost.get())
                session.query(FixedCost).filter_by(id=cost_id).update({"name": name, "cost": cost})
                session.commit()
                messagebox.showinfo("Sukces", f"Zaktualizowano koszt: {name} ({cost:.2f})")
                self.load_fixed_costs()
            except ValueError:
                messagebox.showerror("Błąd", "Proszę podać prawidłową kwotę kosztu")
        else:
            messagebox.showerror("Błąd", "Wybierz koszt do aktualizacji")

    def load_fixed_costs(self):
        self.fixed_costs_tree.delete(*self.fixed_costs_tree.get_children())
        fixed_costs = session.query(FixedCost).all()
        for cost in fixed_costs:
            self.fixed_costs_tree.insert("", "end", values=(cost.name, cost.cost))


if __name__ == "__main__":
    app = Application()
    app.mainloop()
