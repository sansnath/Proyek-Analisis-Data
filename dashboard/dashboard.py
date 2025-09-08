import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import folium
from streamlit_folium import st_folium

best_seller_df = pd.read_csv("/data/best_seller.csv")
customer_order_df = pd.read_csv("/data/customer_order1.csv")
product_review_df = pd.read_csv("/data/product_review.csv")
product_order_df = pd.read_csv("/data/product_order.csv")
payment_method_df = pd.read_csv("/data/payment_method.csv")


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

def create_top_region_df(df):
    top_region_df = (
        df.groupby(["customer_city", "customer_state"])
        .agg({
            "order_id": "count",
            "geolocation_lat": "mean",
            "geolocation_lng": "mean"
        })
        .sort_values(by="order_id", ascending=False)
        .reset_index()
        .head(20)
    )
    top_region_df.columns = ['City', 'State', 'Total Sales', 'Latitude', 'Longitude']
    return top_region_df

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

top_products = create_top_products_df(product_order_df)
st.markdown("<h1 style='text-align: center;'>E-Commerce Dashboard</h1>", unsafe_allow_html=True)
st.subheader('Best Selling Product Category')
fig, ax = plt.subplots(figsize=(10,6))
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
        """Pada Chart ini terlihat bahwa Kategori Produk yang laku di E-Commerce ini adalah kategori
        bet_bed_table dengan diikuti health_beauty dan sports_leisure. E-Commerce bisa mengambil langkah
        untuk membuat strategi baru untuk meningkatkan lagi promosi pada kategori tersebut dan dapat
        melakukan kerjasama dengan brand penyedia barang tersebut supaya dapat memaksimalkan kembali
        pendapatan yang ada.
        """
    )


Top_Region = create_top_region_df(customer_order_df)
map_center = [Top_Region['Latitude'].mean(), Top_Region['Longitude'].mean()]
m = folium.Map(location=map_center, zoom_start=5)

max_sales = Top_Region['Total Sales'].max()

for _, row in Top_Region.iterrows():
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
        """Pada Chart ini terlihat bahwa daerah yang memiliki tingkat pembelian tertinggi memiliki
        diameter lingkaran yang besar, sehingga dapat terlihat daerah mana yang menggunakan E-Commerce
        ini secara masif. Perusahaan bisa mengambil langkah dengan menjadikan wilayah yang besar peminatnya
        sebagai tujuan pasar mereka
        """
    )

Top_Products_Review, Bad_Products_Review = create_product_review_df(product_review_df)
st.subheader("Product Category Performance Overview")
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
        """Pada Chart ini terlihat bahwa kategori produk yang memiliki rating tertinggi adalah berkaitan
        dengan musik, fashion, dan juga buku sejenisnya. Dengan produk terburuk ada di bidang security
        popok dan juga furniture kantor. Hal ini bisa menjadi petunjuk untuk memperkuat kategori barang
        yang memiliki review score tertinggi dan dapat segera meninggalkan kategori barang yang memiliki
        rating rendah
        """
    )

Best_Seller = create_best_seller_df(best_seller_df)
st.subheader("Best Seller Performance Overview")
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(18, 6))
sns.barplot(
    y="Seller_id",
    x="Total Sales",
    data=Best_Seller.sort_values(by="Total Sales", ascending=False),
    palette=sns.color_palette("Blues_r", n_colors=10),
    ax=ax[0]
)
ax[0].set_title("Best Sellers in Terms of Selling", fontsize=15)
ax[0].set_ylabel(None)
ax[0].set_xlabel("Total Sales")
sns.regplot(
    data=Best_Seller,
    x='Total Sales',
    y='Review Score',
    ax=ax[1]
)
ax[1].set_ylim(0, Best_Seller['Review Score'].max() + 1)
ax[1].set_title("Relationship Between Total Sales and Review Score", fontsize=15)
ax[1].set_xlabel("Total Sales")
ax[1].set_ylabel("Review Score")

plt.suptitle("Best Seller Performance Overview", fontsize=20)
plt.tight_layout()
st.pyplot(fig)
with st.expander("See explanation"):
    st.write(
        """Pada Chart ini terlihat bahwa terdapat seller yang memiliki penjualan tertinggi pada 
        E-Commerce ini, perusahaan bisa memberikan suatu benefit ataupun reward yang membuat seller 
        menjadi nyaman untuk terus menggunakan platform E-Commerce ini. Chart ini juga melihatkan bahwa
        seller terbaik tidak sebanding dengan review score yang ada, yang berarti harga barang serta promosi
        dari seller bisa menjadi faktor lain dalam penjualan seller.
        """
    )

st.subheader("Most Used Payment Method")
Popular_Payment_Method = create_popular_payment_df(payment_method_df)

colors = ('#8B4513', '#FFF8DC', '#93C572', '#E67F0D')
explode = [0.05, 0.1, 0.1, 0.1]

fig, ax = plt.subplots(figsize=(6,6))
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
        """Pada Chart ini terlihat bahwa pelanggan seringkali menggunakan kartu kredit sebagai
        media utama pembayaran pada E-Commerce ini, perusahaan bisa memanfaatkan ini dengan bekerjasama
        dengan perusahaan kartu kredit untuk memaksimalkan lagi penggunaan kartu kredit untuk media pembayaran
        pada perusahaan ini
        """
    )
