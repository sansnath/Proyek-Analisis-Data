import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from streamlit_folium import st_folium

all_df = pd.read_csv("dashboard/all_df5.csv")

all_df['order_purchase_timestamp'] = pd.to_datetime(all_df['order_purchase_timestamp'])

st.sidebar.title("Filter Data")

st.sidebar.subheader("Filter by Date Range")
min_date = all_df['order_purchase_timestamp'].min().date()
max_date = all_df['order_purchase_timestamp'].max().date()

start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)

if start_date > end_date:
    st.sidebar.error("End Date must be after Start Date")

st.sidebar.subheader("Filter by Product Category")
product_categories = all_df['product_category_name_english'].unique()
selected_category = st.sidebar.multiselect("Select Category", sorted(product_categories))

filtered_orders = all_df[
    (all_df['order_purchase_timestamp'].dt.date >= start_date) &
    (all_df['order_purchase_timestamp'].dt.date <= end_date)
]

if selected_category:
    filtered_orders = filtered_orders[filtered_orders['product_category_name_english'].isin(selected_category)]

def create_top_products_df(df):
    top_products_df = (
        df.groupby('product_category_name_english')['order_id']
        .nunique()
        .sort_values(ascending=False)
        .reset_index()
        .head(10)
    )
    top_products_df.rename(columns={
        'product_category_name_english': 'product_category',
        'order_id': 'Total Sales'
    }, inplace=True)
    return top_products_df

def create_product_review_df(df):
    top_product_review = (
        df.groupby("product_category_name_english")["review_score"]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
        .head(10)
    )
    bad_product_review = (
        df.groupby("product_category_name_english")["review_score"]
        .mean()
        .sort_values(ascending=True)
        .reset_index()
        .head(10)
    )
    bad_product_review.columns = ['Product Category', 'Review Score']
    top_product_review.columns = ['Product Category', 'Review Score']
    return top_product_review, bad_product_review

def create_best_seller_df(df):
    best_seller_df = (
        df.groupby("seller_id")
        .agg({
            "order_id": "count",
            "review_score": "mean"
        })
        .sort_values(by=["order_id", "review_score"], ascending=False)
        .reset_index()
        .head(10)
    )
    best_seller_df.columns = ['Seller_id', 'Total Sales', 'Review Score']
    return best_seller_df

def create_popular_payment_df(df):
    payment_df = (
        df.groupby("payment_type")["order_id"]
        .count()
        .sort_values(ascending=False)
        .reset_index()
    )
    payment_df.columns = ['Payment Type', 'Total Sales']
    payment_df['Payment Type'] = payment_df['Payment Type'].replace({
        'credit_card': 'Credit Card',
        'boleto': 'Boleto',
        'voucher': 'Voucher',
        'debit_card': 'Debit Card'
    })
    return payment_df

st.markdown("<h1 style='text-align: center;'>E-Commerce Dashboard</h1>", unsafe_allow_html=True)

st.subheader('Best Selling Product Category')
top_products = create_top_products_df(filtered_orders)

fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(
    y="product_category",
    x="Total Sales",
    data=top_products.sort_values(by="Total Sales", ascending=False),
    palette=sns.color_palette("Blues_r", n_colors=10),
    ax=ax
)
ax.set_title("Number of Sales by Product Category", loc="center", fontsize=15)
ax.set_ylabel(None)
st.pyplot(fig)

with st.expander("See explanation"):
    st.write(
        """Kategori produk yang paling laku menunjukkan tren permintaan tertinggi.
        Perusahaan dapat memfokuskan promosi dan kerjasama pada kategori ini untuk
        memaksimalkan pendapatan."""
    )

Top_Region = all_df.groupby(by=["customer_city", "customer_state"]).agg({
    "order_id": "count",
    "geolocation_lat": "mean",
    "geolocation_lng": "mean"
}).sort_values(by="order_id", ascending=False).reset_index()

Top_Region.columns = ['City', 'State', 'Total Sales', 'Latitude', 'Longitude']

map_center = [Top_Region['Latitude'].mean(), Top_Region['Longitude'].mean()]
m = folium.Map(location=map_center, zoom_start=5)

max_sales = Top_Region['Total Sales'].max()

for _, row in Top_Region.head(20).iterrows():
    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=(row['Total Sales'] / max_sales) * 20,
        color='blue',
        fill=True,
        fill_color='blue',
        fill_opacity=0.6,
        popup=f"""
        <b>City:</b> {row['City']}<br>
        <b>State:</b> {row['State']}<br>
        <b>Total Sales:</b> {row['Total Sales']}
        """,
        tooltip=f"{row['City'].upper()} - {row['Total Sales']}"
    ).add_to(m)

st.subheader("Top Region Sales Map")
st_folium(m, width=800, height=500)
with st.expander("See explanation"):
    st.write(
        """Wilayah dengan lingkaran terbesar menunjukkan area dengan tingkat penjualan tertinggi.
        Informasi ini dapat membantu menentukan target pasar dan strategi distribusi."""
    )

st.subheader("Product Category Performance Overview")
Top_Products_Review, Bad_Products_Review = create_product_review_df(filtered_orders)

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(18, 6))

sns.barplot(
    y="Product Category",
    x="Review Score",
    data=Bad_Products_Review.sort_values(by="Review Score", ascending=True),
    palette=sns.color_palette("Blues_r", n_colors=10),
    ax=ax[0]
)
ax[0].set_title("Bad Review Products", loc="center", fontsize=15)
ax[0].set_xlim(0, 5)
ax[0].set_ylabel(None)
ax[0].set_xlabel("Review Score")

sns.barplot(
    y="Product Category",
    x="Review Score",
    data=Top_Products_Review.sort_values(by="Review Score", ascending=False),
    palette=sns.color_palette("Blues_r", n_colors=10),
    ax=ax[1]
)
ax[1].set_title("Good Review Products", loc="center", fontsize=15)
ax[1].set_xlim(0, 5)
ax[1].set_ylabel(None)
ax[1].set_xlabel("Review Score")

plt.tight_layout()
st.pyplot(fig)
with st.expander("See explanation"):
    st.write(
        """Chart ini menampilkan perbandingan kategori dengan review terbaik dan terburuk.
        Fokus pada kategori dengan rating tinggi dan evaluasi produk dengan rating rendah."""
    )

st.subheader("Best Seller Performance Overview")
best_seller_filtered = create_best_seller_df(filtered_orders)

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(18, 6))

sns.barplot(
    y="Seller_id",
    x="Total Sales",
    data=best_seller_filtered.sort_values(by="Total Sales", ascending=False),
    palette=sns.color_palette("Blues_r", n_colors=10),
    ax=ax[0]
)
ax[0].set_title("Best Sellers in Terms of Selling", fontsize=15)
ax[0].set_ylabel(None)
ax[0].set_xlabel("Total Sales")

sns.regplot(
    data=best_seller_filtered,
    x='Total Sales',
    y='Review Score',
    ax=ax[1]
)
ax[1].set_ylim(0, best_seller_filtered['Review Score'].max() + 1)
ax[1].set_title("Sales vs Review Score", fontsize=15)
ax[1].set_xlabel("Total Sales")
ax[1].set_ylabel("Review Score")

plt.suptitle("Best Seller Performance Overview", fontsize=20)
plt.tight_layout()
st.pyplot(fig)
with st.expander("See explanation"):
    st.write(
        """Seller dengan penjualan tertinggi dapat diberi reward untuk meningkatkan loyalitas.
        Hubungan antara total penjualan dan review membantu memahami faktor keberhasilan seller."""
    )


st.subheader("Most Used Payment Method")
Popular_Payment_Method = create_popular_payment_df(filtered_orders)

colors = ('#8B4513', '#FFF8DC', '#93C572', '#E67F0D')
explode = [0.05, 0.1, 0.1, 0.1]

fig, ax = plt.subplots(figsize=(6, 6))
ax.pie(
    x=Popular_Payment_Method['Total Sales'],
    labels=Popular_Payment_Method['Payment Type'],
    autopct='%1.1f%%',
    colors=colors,
    explode=explode,
    textprops={'fontsize': 10}
)
ax.set_title("Popular Payment Method", fontsize=16)

st.pyplot(fig)
with st.expander("See explanation"):
    st.write(
        """Metode pembayaran yang paling sering digunakan dapat menjadi peluang
        untuk menjalin kerja sama, seperti promo kartu kredit atau diskon khusus."""
    )
