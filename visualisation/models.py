from django.db import models

from scraper.models import EbayGraphicsCard


class NvidiaGeneration(models.Model):
    architecture = models.CharField(max_length=80)  # Ampere
    series = models.CharField(max_length=80)  # GeForce 30 series
    year = models.IntegerField(verbose_name="Release year")

    class Meta:
        unique_together = (
            "architecture",
            "series",
        )

    def __str__(self) -> str:
        return f"{self.series} | {self.architecture}"


class GraphicsCard(models.Model):
    model = models.CharField(max_length=80)  # GeForce RTX 3060
    short_model = models.CharField(max_length=20)  # 3060
    architecture = models.ForeignKey(
        NvidiaGeneration, on_delete=models.CASCADE
    )
    launch_date = models.DateField()
    launch_price = models.IntegerField(verbose_name="Launch price ($)")
    memory_size = models.IntegerField(verbose_name="Memory size (MB)")
    memory_size_restrict = models.BooleanField(default=False)
    ti = models.BooleanField(default=False)
    ti_restrict = models.BooleanField(default=False)
    super = models.BooleanField(default=False)
    super_restrict = models.BooleanField(default=False)
    tdp = models.IntegerField(
        verbose_name="TDP (Watts)", blank=True, null=True
    )  # In Watts
    g3d_mark_median = models.IntegerField(verbose_name="G3DMark median score")
    passmark_samples = models.IntegerField()

    def __str__(self) -> str:
        return f"{self.model}"

    class Meta:
        unique_together = ("model",)


class GraphicsCardLink(models.Model):
    model = models.ForeignKey(GraphicsCard, on_delete=models.CASCADE)
    ebay_gpu = models.ForeignKey(EbayGraphicsCard, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("model", "ebay_gpu")

    def __str__(self):
        return f"{self.ebay_gpu.name} --> {self.model.model}"


class Sale(models.Model):
    gpu = models.ForeignKey(GraphicsCard, on_delete=models.CASCADE)
    title = models.CharField(max_length=80)
    date = models.DateTimeField()
    total_price = models.FloatField()
    outlier = models.BooleanField(default=False)
    founders = models.BooleanField(default=False)

    def __str__(self):
        return f"£{self.total_price:7.2f} | {self.title}"
