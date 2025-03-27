class VoidRecord(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='void_records')
    item = models.ForeignKey(TransactionDetail, on_delete=models.CASCADE)
    voided_by = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    void_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-void_date']

    def __str__(self):
        return f"Voided {self.item.product.name} from Transaction #{self.transaction.trans_id}" 