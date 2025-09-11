import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from streamlit_folium import st_folium

all_df = pd.read_csv("dashboard/all_df10.csv")

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
total_orders = filtered_orders['order_id'].count()
unique_customers = filtered_orders['customer_id'].nunique()
average_review = filtered_orders['review_score'].mean()
unique_categories = filtered_orders['product_category_name_english'].nunique()

st.markdown("### Key Metrics Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Orders", f"{total_orders:,}")

with col2:
    st.metric("Total Customers", f"{unique_customers:,}")

with col3:
    st.metric("Avg. Review Score", f"{average_review:.2f}")

with col4:
    st.metric("Product Categories", f"{unique_categories:,}")

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
min_sales = Top_Region['Total Sales'].min()

colormap = cm.get_cmap('RdYlBu_r') 
def get_color(value):
    normalized_value = (value - min_sales) / (max_sales - min_sales) 
    rgba_color = colormap(normalized_value)
    return mcolors.to_hex(rgba_color)  

for _, row in Top_Region.head(20).iterrows():
    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=(row['Total Sales'] / max_sales) * 20,  
        color=get_color(row['Total Sales']),           
        fill=True,
        fill_color=get_color(row['Total Sales']),
        fill_opacity=0.7,
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
        """
        Lingkaran **lebih besar dan lebih gelap** menunjukkan wilayah dengan **penjualan yang lebih tinggi**.
        Warna membantu membedakan tingkat penjualan, sehingga mudah mengidentifikasi kota dengan performa terbaik.
        """
    )

st.subheader("Product Category Performance Overview")
Top_Products_Review, Bad_Products_Review = create_product_review_df(filtered_orders)

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(18, 6))

Bad_Products_Review = Bad_Products_Review.sort_values(by="Review Score", ascending=True).reset_index(drop=True)

bad_colors = ['red' if i < 3 else 'lightgray' for i in range(len(Bad_Products_Review))]

sns.barplot(
    y="Product Category",
    x="Review Score",
    data=Bad_Products_Review,
    palette=bad_colors,
    ax=ax[0]
)
ax[0].set_title("Bad Review Products", loc="center", fontsize=15)
ax[0].set_xlim(0, 5)
ax[0].set_ylabel(None)
ax[0].set_xlabel("Review Score")

Top_Products_Review = Top_Products_Review.sort_values(by="Review Score", ascending=False).reset_index(drop=True)

good_colors = ['green' if i < 3 else 'lightgray' for i in range(len(Top_Products_Review))]

sns.barplot(
    y="Product Category",
    x="Review Score",
    data=Top_Products_Review,
    palette=good_colors,
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
        """
        Chart ini menampilkan kategori produk dengan review terbaik dan terburuk.
        - **Hijau** menunjukkan 3 produk dengan review terbaik.
        - **Merah** menunjukkan 3 produk dengan review terburuk.
        - **Abu-abu** digunakan untuk kategori lain agar fokus tetap terlihat pada yang paling penting.
        
        Visualisasi ini membantu tim untuk fokus meningkatkan kualitas produk yang memiliki ulasan buruk
        serta memaksimalkan potensi dari produk dengan ulasan terbaik.
        """
    )

st.subheader("Best Seller Performance Overview")
best_seller_filtered = create_best_seller_df(filtered_orders)

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(18, 6))

sns.barplot(
    y="Seller_id",
    x="Total Sales",
    data=best_seller_filtered.head(10).sort_values(by="Total Sales", ascending=False),
    palette=sns.color_palette("Blues_r", n_colors=10),
    ax=ax[0]
)
ax[0].set_title("Best Sellers in Terms of Selling", fontsize=15)
ax[0].set_ylabel(None)
ax[0].set_xlabel("Total Sales")

_, bins = pd.qcut(
    best_seller_filtered['Total Sales'],
    q=4,
    retbins=True,
    duplicates='drop'
)

labels_map = ['Low', 'Medium', 'High', 'Very High']
labels_used = labels_map[:len(bins)-1]

best_seller_filtered['Sales_Category'] = pd.qcut(
    best_seller_filtered['Total Sales'],
    q=4,
    labels=labels_used,
    duplicates='drop'
)
sns.boxplot(
    data=best_seller_filtered,
    x='Sales_Category',
    y='Review Score',
    ax=ax[1]
)
ax[1].set_ylim(0, best_seller_filtered['Review Score'].max() + 1)
ax[1].set_title("Relationship Between Total Sales and Review Score", fontsize=15)
ax[1].set_xlabel("Total Sales")
ax[1].set_ylabel("Review Score")

plt.suptitle("Best Seller Performance Overview", fontsize=20)
plt.tight_layout()
st.pyplot(fig)
with st.expander("See explanation"):
    st.write(
        """Seller dengan penjualan tertinggi dapat diberi reward untuk meningkatkan loyalitas.
        Chart ini juga melihatkan bahwa terdapat hubungan antara jumlah sales dengan rating yang dapat dilihat pada chart boxplot."""
    )


st.subheader("Most Used Payment Method")
Popular_Payment_Method = create_popular_payment_df(filtered_orders)

colors = ("#6495E5", '#4682B4', '#87CEEB', '#B0E0E6')
explode = [0.05, 0.1, 0.1, 0.1]

fig, ax = plt.subplots(figsize=(6, 6))
ax.pie(
    x=Popular_Payment_Method['Total Sales'],
    labels=Popular_Payment_Method['Payment Type'],
    autopct='%1.1f%%',
    colors=colors,
    explode=explode,
    textprops={'fontsize': 10},
)
ax.set_title("Popular Payment Method", fontsize=16)

st.pyplot(fig)
with st.expander("See explanation"):
    st.write(
        """Metode pembayaran yang paling sering digunakan dapat menjadi peluang
        untuk menjalin kerja sama, seperti promo kartu kredit atau diskon khusus."""
    )
