from django.db import transaction
from .models import Product, Supplier

def add_supplier_to_products(supplier_id, product_ids):
    """
    Associates a single supplier with multiple products.
    
    Args:
        supplier_id (int): The ID of the supplier to add
        product_ids (list): A list of product IDs to associate with the supplier
        
    Returns:
        int: The number of products that were processed
    """
    try:
        # Get the supplier
        supplier = Supplier.objects.get(id=supplier_id)
        
        # Get the products
        products = Product.objects.filter(id__in=product_ids)
        
        # Count before adding to know how many products we're processing
        product_count = products.count()
        
        if product_count == 0:
            return 0  # No products found
            
        # Add the supplier to all products in a single operation
        supplier.products.add(*products)
        
        return product_count
        
    except Supplier.DoesNotExist:
        # Handle the case where the supplier doesn't exist
        raise ValueError(f"Supplier with ID {supplier_id} does not exist")
    except Exception as e:
        # Handle other exceptions
        raise e