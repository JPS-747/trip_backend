import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useApiConfig } from '@/contexts/ApiConfigContext'
import { getHolidays } from '@/services/holidayService'
import type { HolidayRecord } from '@/services/holidayService'

const HolidaysPage = () => {
    const { apiBaseUrl } = useApiConfig()
    const [currentYearIndex, setCurrentYearIndex] = useState(0)

    const { data: holidaysData, isLoading, isError, error } = useQuery({
        queryKey: ['holidays', apiBaseUrl],
        queryFn: () => getHolidays(apiBaseUrl),
    })

    // Group holidays by year
    const holidaysByYear = useMemo(() => {
        if (!holidaysData?.holidays) return {}

        const grouped: Record<number, HolidayRecord[]> = {}

        holidaysData.holidays.forEach((holiday) => {
            const year = new Date(holiday.date).getFullYear()
            if (!grouped[year]) {
                grouped[year] = []
            }
            grouped[year].push(holiday)
        })

        // Sort holidays within each year by date
        Object.keys(grouped).forEach((year) => {
            grouped[parseInt(year)].sort((a, b) =>
                new Date(a.date).getTime() - new Date(b.date).getTime()
            )
        })

        return grouped
    }, [holidaysData?.holidays])

    const sortedYears = useMemo(() => {
        return Object.keys(holidaysByYear)
            .map(Number)
            .sort((a, b) => a - b)
    }, [holidaysByYear])

    const currentYear = sortedYears[currentYearIndex]
    const currentYearHolidays = currentYear ? holidaysByYear[currentYear] : []

    const handlePreviousYear = () => {
        setCurrentYearIndex((prev) => Math.max(0, prev - 1))
    }

    const handleNextYear = () => {
        setCurrentYearIndex((prev) => Math.min(sortedYears.length - 1, prev + 1))
    }

    const handleFirstYear = () => {
        setCurrentYearIndex(0)
    }

    const handleLastYear = () => {
        setCurrentYearIndex(sortedYears.length - 1)
    }

    const handleSelectYear = (year: number) => {
        const index = sortedYears.indexOf(year)
        if (index !== -1) {
            setCurrentYearIndex(index)
        }
    }

    if (isLoading) {
        return (
            <div className="page-content">
                <section className="panel">
                    <h1>Public Holidays</h1>
                    <p>Loading holidays…</p>
                </section>
            </div>
        )
    }

    if (isError) {
        return (
            <div className="page-content">
                <section className="panel">
                    <h1>Public Holidays</h1>
                    <p style={{ color: 'var(--danger)' }}>
                        Failed to load holidays: {error instanceof Error ? error.message : 'Unknown error'}
                    </p>
                </section>
            </div>
        )
    }

    return (
        <div className="page-content">
            <section className="panel">
                <h1>Namibia Public Holidays</h1>
                <p className="subtitle">Browse public holidays by year</p>

                {sortedYears.length === 0 ? (
                    <p>No holidays found.</p>
                ) : (
                    <>
                        <div style={{ marginBottom: '2rem' }}>
                            <h2 style={{ marginBottom: '1rem' }}>Year {currentYear}</h2>
                            <p style={{ marginBottom: '1rem', opacity: 0.8 }}>
                                {currentYearHolidays.length} holiday{currentYearHolidays.length !== 1 ? 's' : ''} in {currentYear}
                            </p>

                            <div className="table-wrap">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Date</th>
                                            <th>Holiday Name</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {currentYearHolidays.map((holiday, idx) => {
                                            const date = new Date(holiday.date)
                                            const formattedDate = date.toLocaleDateString('en-US', {
                                                weekday: 'short',
                                                year: 'numeric',
                                                month: 'short',
                                                day: 'numeric',
                                            })

                                            return (
                                                <tr key={idx}>
                                                    <td style={{ whiteSpace: 'nowrap', fontWeight: 500 }}>
                                                        {formattedDate}
                                                    </td>
                                                    <td>{holiday.name}</td>
                                                </tr>
                                            )
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        {/* Year Navigation */}
                        <div className="action-row" style={{ justifyContent: 'center', gap: '0.5rem', marginTop: '2rem', flexWrap: 'wrap' }}>
                            {/* First year button */}
                            <button
                                className="button secondary"
                                type="button"
                                onClick={handleFirstYear}
                                disabled={currentYearIndex === 0}
                                title="First year"
                                style={{ minWidth: '44px' }}
                            >
                                {'<<'}
                            </button>

                            {/* Previous year button */}
                            <button
                                className="button secondary"
                                type="button"
                                onClick={handlePreviousYear}
                                disabled={currentYearIndex === 0}
                                title="Previous year"
                                style={{ minWidth: '44px' }}
                            >
                                {'<'}
                            </button>

                            {/* Year selection buttons */}
                            <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap', justifyContent: 'center' }}>
                                {sortedYears.map((year) => (
                                    <button
                                        key={year}
                                        className={year === currentYear ? 'button' : 'button secondary'}
                                        type="button"
                                        onClick={() => handleSelectYear(year)}
                                        style={{
                                            minWidth: '60px',
                                            fontWeight: year === currentYear ? 'bold' : 'normal',
                                        }}
                                    >
                                        {year}
                                    </button>
                                ))}
                            </div>

                            {/* Next year button */}
                            <button
                                className="button secondary"
                                type="button"
                                onClick={handleNextYear}
                                disabled={currentYearIndex === sortedYears.length - 1}
                                title="Next year"
                                style={{ minWidth: '44px' }}
                            >
                                {'>'}
                            </button>

                            {/* Last year button */}
                            <button
                                className="button secondary"
                                type="button"
                                onClick={handleLastYear}
                                disabled={currentYearIndex === sortedYears.length - 1}
                                title="Last year"
                                style={{ minWidth: '44px' }}
                            >
                                {'>>'}
                            </button>

                            {/* Year info */}
                            <span className="status-text" style={{ marginLeft: '1rem' }}>
                                Year {currentYearIndex + 1} of {sortedYears.length}
                            </span>
                        </div>

                        {/* Summary */}
                        <div style={{ marginTop: '2rem', padding: '1rem', backgroundColor: 'var(--bg-secondary)', borderRadius: '0.5rem' }}>
                            <h3 style={{ marginBottom: '0.5rem' }}>Summary</h3>
                            <p style={{ marginBottom: '0.5rem' }}>
                                <strong>Total Years:</strong> {sortedYears.length} (from {sortedYears[0]} to {sortedYears[sortedYears.length - 1]})
                            </p>
                            <p>
                                <strong>Total Holidays:</strong> {holidaysData?.holidays?.length ?? 0}
                            </p>
                        </div>
                    </>
                )}
            </section>
        </div>
    )
}

export default HolidaysPage
