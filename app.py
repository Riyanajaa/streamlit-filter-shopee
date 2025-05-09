import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Filter Produk", layout="wide")

# === CSS untuk tema gelap tetap ===
st.markdown("""
    <style>
        body {
            background-color: #1e1e1e;
            color: #e0e0e0;
        }
        .reportview-container .main .block-container {
            background-color: #1e1e1e;
            color: #e0e0e0;
        }
        .sidebar .sidebar-content {
            background-color: #2a2a2a;
        }
        .section-title {
            font-size: 1.4em;
            font-weight: bold;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            color: #99ddff;
        }
        .stat-box {
            background-color: #333;
            padding: 1em;
            border-radius: 10px;
            margin-bottom: 1em;
            border: 1px solid #99ddff;
            color: #e0e0e0;
        }
        .stat-box ul { padding-left: 1.2em; }
        .stat-box li { margin-bottom: 0.4em; }
        .stButton>button {
            background-color: #99ddff;
            color: black;
            border: none;
            padding: 0.5em 1em;
            border-radius: 4px;
            font-weight: bold;
        }
        .stButton>button:hover {
            transform: scale(1.05);
        }
        .stTextInput>div>input, .stNumberInput>div>input {
            background-color: #2e2e2e;
            color: #e0e0e0;
            border: 1px solid #99ddff;
        }
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: #1e1e1e;
            color: #ccc;
            text-align: center;
            padding: 1em;
            font-size: 0.9em;
            font-style: italic;
            border-top: 1px solid #99ddff;
        }
    </style>
""", unsafe_allow_html=True)

# === INPUT FILTER DI SIDEBAR ===
st.sidebar.title("🚬 ADIT GANTENG")
stok_min = st.sidebar.number_input("Batas minimal stok", min_value=0, value=10)
terjual_min = st.sidebar.number_input("Batas minimal terjual per bulan", min_value=0, value=100)
harga_min = st.sidebar.number_input("Batas minimal harga produk", min_value=0.0, value=20000.0)
komisi_persen_min = st.sidebar.number_input("Batas minimal komisi (%)", min_value=0.0, value=1.0)
komisi_rp_min = st.sidebar.number_input("Batas minimal komisi (Rp)", min_value=0.0, value=1000.0)

uploaded_files = st.file_uploader("Masukan File Format (.txt)", type=["txt"], accept_multiple_files=True)

# === FUNGSI PEMBACAAN DAN FILTER ===
def read_and_validate_file(uploaded_file):
    try:
        content = uploaded_file.read().decode('utf-8')
        df = pd.read_csv(io.StringIO(content), delimiter='\t', on_bad_lines='skip')
        df['source_file'] = uploaded_file.name
        if 'Link Produk' not in df.columns:
            df['Link Produk'] = 'Link tidak tersedia'
        for col in ['Harga', 'Stock', 'Terjual(Bulanan)', 'Komisi(%)', 'Komisi(Rp)']:
            if col not in df.columns:
                st.warning(f"Kolom '{col}' tidak ditemukan di {uploaded_file.name}, akan diisi 0.")
                df[col] = 0
        return df
    except Exception as e:
        st.error(f"Gagal membaca {uploaded_file.name}: {e}")
        return None

def preprocess_data(df):
    df['Harga'] = pd.to_numeric(df['Harga'], errors='coerce').fillna(0)
    df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0)
    df['Terjual(Bulanan)'] = pd.to_numeric(df['Terjual(Bulanan)'], errors='coerce').fillna(0)
    df['Komisi(%)'] = pd.to_numeric(df['Komisi(%)'].astype(str).str.replace('%', ''), errors='coerce').fillna(0)
    df['Komisi(Rp)'] = pd.to_numeric(df['Komisi(Rp)'], errors='coerce').fillna(0)
    return df

def apply_filters(df):
    return df[
        (df['Stock'] >= stok_min) & 
        (df['Terjual(Bulanan)'] >= terjual_min) & 
        (df['Harga'] >= harga_min) & 
        (df['Komisi(%)'] >= komisi_persen_min) & 
        (df['Komisi(Rp)'] >= komisi_rp_min)
    ]

# === PROSES DATA ===
if uploaded_files and st.button("🚀 Proses Data"):
    with st.spinner("⏳ Memproses data..."):
        combined_df = pd.DataFrame()

        for file in uploaded_files:
            df = read_and_validate_file(file)
            if df is not None:
                combined_df = pd.concat([combined_df, df], ignore_index=True)

        if not combined_df.empty:
            total_links = len(combined_df)
            combined_df.drop_duplicates(subset=['Link Produk'], inplace=True)
            deleted_dupes = total_links - len(combined_df)

            combined_df = preprocess_data(combined_df)
            filtered_df = apply_filters(combined_df)
            removed_df = combined_df[~combined_df.index.isin(filtered_df.index)]

            # Menghitung trend dengan pembatasan dua desimal
            filtered_df['Trend'] = (filtered_df['Terjual(Bulanan)'] / filtered_df['Terjual(Semua)'] * 100).round(2)

            # Menentukan status
            def get_status(row):
                if row['Trend'] >= 10:
                    return 'Trending🔥'
                elif row['Trend'] >= 2:
                    return 'Stabil 👍'
                elif row['Trend'] < 2 and row['Trend'] > 0:
                    return 'Menurun ❌'
                else:
                    return 'NEW PRODUK '

            filtered_df['Status'] = filtered_df.apply(get_status, axis=1)

            st.success("✅ Data berhasil diproses!")

            st.markdown(f"""
            <div class="stat-box">
                <div class="section-title">📊 Statistik</div>
                <ul>
                    <li>Total produk diproses: <strong>{total_links}</strong></li>
                    <li>Produk unik setelah hapus duplikat: <strong>{len(combined_df)}</strong></li>
                    <li>Produk lolos filter: <strong>{len(filtered_df)}</strong></li>
                    <li>Produk tidak lolos filter: <strong>{len(removed_df)}</strong></li>
                    <li>Duplikat yang dihapus: <strong>{deleted_dupes}</strong></li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            st.subheader("✅ Final Produk")
            st.dataframe(filtered_df)
            st.download_button("⬇️ Download Data Produk", filtered_df.to_csv(index=False).encode('utf-8'), file_name="data_produk.csv", mime='text/csv')

            st.subheader("🗑️ Produk Dihapus")
            st.dataframe(removed_df)
            st.download_button("⬇️ Download sampah", removed_df.to_csv(index=False).encode('utf-8'), file_name="sampah.csv", mime='text/csv')
        else:
            st.warning("Tidak ada data valid yang bisa diproses.")

# === FEEDBACK SECTION ===
show_feedback = st.checkbox("💬 Kritik & Saran", value=False)
if show_feedback:
    feedback = st.text_area("Tulis kritik atau saran kamu di sini:")
    if st.button("Kirim"):
        st.success("🎉 Terima kasih atas masukannya!")

# === FOOTER ===
st.markdown("""
    <div class="footer">
        &copy; 2025 - Dibuat oleh Wong Sukses
    </div>
""", unsafe_allow_html=True)
