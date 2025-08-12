export const dateUtils = {
  formatDate(date: string | Date): string {
    const d = new Date(date);
    return d.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  },

  isDateAfter(date1: string | Date, date2: string | Date): boolean {
    return new Date(date1) > new Date(date2);
  },

  addMonths(date: string | Date, months: number): Date {
    const d = new Date(date);
    d.setMonth(d.getMonth() + months);
    return d;
  },

  isDonorAvailable(lastDonationDate?: string): boolean {
    if (!lastDonationDate) return true;
    
    const fourMonthsLater = this.addMonths(lastDonationDate, 4);
    return new Date() >= fourMonthsLater;
  },

  getDaysUntilAvailable(lastDonationDate: string): number {
    const fourMonthsLater = this.addMonths(lastDonationDate, 4);
    const diffTime = fourMonthsLater.getTime() - new Date().getTime();
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  }
};