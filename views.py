from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
import json
from django.utils import timezone

@login_required
def void_item(request):
    return render(request, 'void_item.html')

@login_required
def search_transactions(request):
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({
            'success': False,
            'error': 'Search query too short'
        })
    
    try:
        transactions = Transaction.objects.filter(
            Q(trans_id__icontains=query) |
            Q(user__username__icontains=query)
        ).order_by('-trans_date')[:10]
        
        transactions_data = [{
            'id': trans.trans_id,
            'date': trans.trans_date.strftime('%Y-%m-%d %H:%M'),
            'items_count': trans.details.count(),
            'total_amount': float(trans.total_amt),
            'cashier': trans.user.username
        } for trans in transactions]
        
        return JsonResponse({
            'success': True,
            'transactions': transactions_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def get_transaction_details(request, trans_id):
    try:
        transaction = Transaction.objects.get(trans_id=trans_id)
        items = transaction.details.all()
        
        items_data = [{
            'id': item.id,
            'product_name': item.product.name,
            'quantity': item.quantity,
            'price': float(item.price),
            'subtotal': float(item.subtotal)
        } for item in items]
        
        return JsonResponse({
            'success': True,
            'transaction': {
                'id': transaction.trans_id,
                'date': transaction.trans_date.strftime('%Y-%m-%d %H:%M'),
                'total_amount': float(transaction.total_amt),
                'items': items_data
            }
        })
    except Transaction.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Transaction not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def void_transaction_item(request):
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Invalid request method'
        })
    
    try:
        data = json.loads(request.body)
        transaction_id = data.get('transaction_id')
        item_id = data.get('item_id')
        reason = data.get('reason')
        
        if not all([transaction_id, item_id, reason]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            })
        
        transaction = Transaction.objects.get(trans_id=transaction_id)
        item = transaction.details.get(id=item_id)
        
        # Create void record
        VoidRecord.objects.create(
            transaction=transaction,
            item=item,
            voided_by=request.user,
            reason=reason
        )
        
        # Update transaction total
        transaction.total_amt -= item.subtotal
        transaction.save()
        
        # Delete the item
        item.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Item voided successfully'
        })
    except Transaction.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Transaction not found'
        })
    except TransactionDetail.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Item not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def employee_dashboard(request):
    # Get today's date in the correct timezone
    today = timezone.localtime(timezone.now()).date()
    
    # Get recent transactions (last 5) with correct timezone
    recent_transactions = Transaction.objects.filter(
        trans_date__date=today
    ).order_by('-trans_date')[:5]
    
    # Calculate today's statistics
    today_transactions = Transaction.objects.filter(trans_date__date=today)
    today_sales_count = today_transactions.count()
    today_sales_amount = sum(trans.total_amt for trans in today_transactions)
    
    # Calculate average items per sale
    if today_sales_count > 0:
        total_items = sum(trans.details.count() for trans in today_transactions)
        average_items = round(total_items / today_sales_count, 1)
    else:
        average_items = 0
    
    context = {
        'recent_transactions': recent_transactions,
        'today_sales_count': today_sales_count,
        'today_sales_amount': today_sales_amount,
        'average_items': average_items,
    }
    
    return render(request, 'employee_dashboard.html', context) 