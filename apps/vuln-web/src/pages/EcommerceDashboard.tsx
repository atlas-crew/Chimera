import React, { useState, useEffect } from 'react';
import {
  ShoppingBag,
  Search,
  ShoppingCart,
  Star,
  Package,
  Truck
} from 'lucide-react';

export const EcommerceDashboard: React.FC = () => {
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchProducts = async (query = '') => {
    setLoading(true);
    // Vulnerable search endpoint
    const url = query 
      ? `/api/v1/ecommerce/products/search?query=${encodeURIComponent(query)}`
      : '/api/v1/ecommerce/products';

    try {
      const res = await fetch(url);
      const data = await res.json();
      setProducts(data.products || data.results || []);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchProducts(searchQuery);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-2">
            <ShoppingBag className="w-8 h-8 text-orange-500" />
            ShopRight Retail
          </h1>
          <p className="text-slate-500">Premium Goods & Electronics</p>
        </div>
        
        <div className="flex items-center gap-4 w-full md:w-auto">
          <form onSubmit={handleSearch} className="relative flex-grow md:flex-grow-0 md:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input 
              type="text" 
              placeholder="Search catalog..." 
              className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 transition-all"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
            />
          </form>
          <button className="relative p-2 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">
            <ShoppingCart className="w-5 h-5 text-slate-700" />
            <span className="absolute -top-1 -right-1 w-4 h-4 bg-orange-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">2</span>
          </button>
        </div>
      </div>

      {/* Hero Banner */}
      {searchQuery && (
        <div className="bg-orange-50 border border-orange-200 p-4 rounded-lg mb-6">
          <p className="text-orange-800 text-sm">
            Search results for: <span className="font-bold" dangerouslySetInnerHTML={{ __html: searchQuery }} />
          </p>
        </div>
      )}
      <div className="bg-gradient-to-r from-orange-500 to-pink-500 rounded-2xl p-8 text-white mb-10 shadow-lg relative overflow-hidden">
        <div className="relative z-10 max-w-lg">
          <span className="bg-white/20 backdrop-blur-sm text-xs font-bold px-2 py-1 rounded mb-2 inline-block">SUMMER SALE</span>
          <h2 className="text-3xl font-extrabold mb-2">Up to 50% Off Electronics</h2>
          <p className="mb-6 opacity-90">Get the latest gadgets at unbeatable prices. Limited time offer.</p>
          <button className="bg-white text-orange-600 px-6 py-2 rounded-lg font-bold hover:bg-orange-50 transition-colors">Shop Now</button>
        </div>
        <div className="absolute right-0 top-0 h-full w-1/3 bg-white/10 skew-x-12 translate-x-12" />
      </div>

      {/* Product Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {loading ? (
          <div className="col-span-full text-center py-12 text-slate-400">Loading catalog...</div>
        ) : products.length === 0 ? (
          <div className="col-span-full text-center py-12 text-slate-400">No products found.</div>
        ) : (
          products.map((product: any) => (
            <div key={product.product_id} className="bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow overflow-hidden group">
              <div className="h-48 bg-slate-100 flex items-center justify-center relative">
                <Package className="w-16 h-16 text-slate-300 group-hover:scale-110 transition-transform duration-300" />
                {Math.random() > 0.7 && (
                  <span className="absolute top-2 left-2 bg-red-500 text-white text-[10px] font-bold px-2 py-1 rounded">-20%</span>
                )}
              </div>
              <div className="p-4">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-bold text-slate-900 line-clamp-1">{product.name || `Product ${product.product_id}`}</h3>
                  <div className="flex items-center gap-1 text-xs font-bold text-orange-500">
                    <Star className="w-3 h-3 fill-current" />
                    4.5
                  </div>
                </div>
                <p className="text-xs text-slate-500 mb-4 line-clamp-2">High-quality item suitable for all your needs. Verification pending.</p>
                <div className="flex items-center justify-between">
                  <span className="text-lg font-bold text-slate-900">${product.price || '29.99'}</span>
                  <button className="px-3 py-1.5 bg-slate-900 text-white text-xs font-bold rounded hover:bg-slate-800 transition-colors">
                    Add
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Vendor Section */}
      <div className="mt-16 border-t border-slate-200 pt-10">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-slate-900">Featured Vendors</h2>
          <a href="#" className="text-sm font-medium text-orange-600 hover:text-orange-700">View Marketplace →</a>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map(i => (
            <div key={i} className="flex items-center gap-4 p-4 rounded-lg bg-slate-50 border border-slate-100">
              <div className="w-12 h-12 rounded-full bg-white border border-slate-200 flex items-center justify-center">
                <Truck className="w-6 h-6 text-slate-400" />
              </div>
              <div>
                <h4 className="font-bold text-slate-900">Global Tech {i}</h4>
                <p className="text-xs text-slate-500">98% Positive Feedback</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};