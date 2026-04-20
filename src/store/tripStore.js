import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

export const useTripStore = create(
  persist(
    (set, get) => ({
      tripData: {
        departure: null,
        destination: null,
        departureTime: null,
        returnTime: null,
        departureCoords: null,
        destinationCoords: null
      },

      planResult: null,
      drafts: [],
      currentTripId: null,
      users: [],

      setDeparture: (location, coords) => set((state) => ({
        tripData: { ...state.tripData, departure: location, departureCoords: coords }
      })),

      setDestination: (location, coords) => set((state) => ({
        tripData: { ...state.tripData, destination: location, destinationCoords: coords }
      })),

      setDepartureTime: (time) => set((state) => ({
        tripData: { ...state.tripData, departureTime: time }
      })),

      setReturnTime: (time) => set((state) => ({
        tripData: { ...state.tripData, returnTime: time }
      })),

      resetTripData: () => set({
        tripData: {
          departure: null,
          destination: null,
          departureTime: null,
          returnTime: null,
          departureCoords: null,
          destinationCoords: null
        }
      }),

      saveDraft: (draft) => set((state) => {
        const existingIndex = state.drafts.findIndex((d) => d.id === draft.id)
        if (existingIndex >= 0) {
          const nextDrafts = [...state.drafts]
          nextDrafts[existingIndex] = draft
          return { drafts: nextDrafts, currentTripId: draft.id }
        }

        return {
          drafts: [draft, ...state.drafts],
          currentTripId: draft.id
        }
      }),

      deleteDraft: (draftId) => set((state) => ({
        drafts: state.drafts.filter((d) => d.id !== draftId),
        currentTripId: state.currentTripId === draftId ? null : state.currentTripId
      })),

      loadDraft: (draftId) => set((state) => {
        const draft = state.drafts.find((d) => d.id === draftId)
        if (!draft) return {}

        return {
          currentTripId: draft.id,
          tripData: {
            departure: draft.departure,
            destination: draft.destination,
            departureTime: draft.departureTime,
            returnTime: draft.returnTime,
            departureCoords: draft.departureCoords || null,
            destinationCoords: draft.destinationCoords || null
          },
          planResult: draft.content || null
        }
      }),

      setCurrentTripId: (id) => set({ currentTripId: id }),

      setPlanResult: (result) => set({ planResult: result }),

      // ============ 选项切换方法 ============

      selectTransportOutbound: (index) => set((state) => {
        if (!state.planResult?.structured_plan?.transport?.outbound) return {}
        
        const outbound = state.planResult.structured_plan.transport.outbound
        const nextOption = outbound.options?.[index] || outbound.options?.[0] || null
        
        return {
          planResult: JSON.parse(JSON.stringify({
            ...state.planResult,
            structured_plan: {
              ...state.planResult.structured_plan,
              transport: {
                ...state.planResult.structured_plan.transport,
                outbound: {
                  ...outbound,
                  selected_index: index,
                  selectedIndex: index,
                  selected_option: nextOption,
                  selectedOption: nextOption
                }
              }
            }
          }))
        }
      }),

      selectTransportReturn: (index) => set((state) => {
        if (!state.planResult?.structured_plan?.transport?.return) return {}
        
        const returnPlan = state.planResult.structured_plan.transport.return
        const nextOption = returnPlan.options?.[index] || returnPlan.options?.[0] || null
        
        return {
          planResult: JSON.parse(JSON.stringify({
            ...state.planResult,
            structured_plan: {
              ...state.planResult.structured_plan,
              transport: {
                ...state.planResult.structured_plan.transport,
                return: {
                  ...returnPlan,
                  selected_index: index,
                  selectedIndex: index,
                  selected_option: nextOption,
                  selectedOption: nextOption
                }
              }
            }
          }))
        }
      }),

      selectMealRestaurant: (mealIndex, restaurantIndex) => set((state) => {
        if (!state.planResult?.structured_plan?.foods?.[mealIndex]) return {}
        
        const foods = state.planResult.structured_plan.foods
        const meal = foods[mealIndex]
        const nextOption = meal.options?.[restaurantIndex] || meal.options?.[0] || null
        
        const nextFoods = foods.map((item, idx) =>
          idx === mealIndex
            ? {
                ...item,
                selected_index: restaurantIndex,
                selectedIndex: restaurantIndex,
                selected_option: nextOption,
                selectedOption: nextOption
              }
            : item
        )
        
        return {
          planResult: JSON.parse(JSON.stringify({
            ...state.planResult,
            structured_plan: {
              ...state.planResult.structured_plan,
              foods: nextFoods
            }
          }))
        }
      }),

      selectHotel: (hotelIndex) => set((state) => {
        if (!state.planResult?.structured_plan?.hotels) return {}
        
        const hotels = state.planResult.structured_plan.hotels
        const nextOption = hotels.options?.[hotelIndex] || hotels.options?.[0] || null
        
        return {
          planResult: JSON.parse(JSON.stringify({
            ...state.planResult,
            structured_plan: {
              ...state.planResult.structured_plan,
              hotels: {
                ...hotels,
                selected_index: hotelIndex,
                selectedIndex: hotelIndex,
                selected_option: nextOption,
                selectedOption: nextOption
              }
            }
          }))
        }
      }),

      // ============ 价格计算 ============

      getTotalPrice: () => {
        const state = get()
        if (!state.planResult?.structured_plan) return 0

        const plan = state.planResult.structured_plan
        let total = 0

        // 交通
        if (plan.transport?.outbound?.selected_option) {
          total += plan.transport.outbound.selected_option.estimated_price
        }
        if (plan.transport?.return?.selected_option) {
          total += plan.transport.return.selected_option.estimated_price
        }

        // 景点
        if (plan.attractions) {
          total += plan.attractions.reduce((sum, attr) => sum + (attr.estimated_price_value || 0), 0)
        }

        // 饮食
        if (plan.foods) {
          total += plan.foods.reduce((sum, meal) => {
            if (meal.selected_option) {
              return sum + meal.selected_option.estimated_price
            }
            return sum
          }, 0)
        }

        // 住宿
        if (plan.hotels?.selected_option && state.tripData.departureTime && state.tripData.returnTime) {
          const start = new Date(state.tripData.departureTime)
          const end = new Date(state.tripData.returnTime)
          const nights = Math.max(1, Math.ceil((end - start) / (1000 * 60 * 60 * 24)))
          total += plan.hotels.selected_option.estimated_price * nights
        }

        return total
      },

      getPricingBreakdown: () => {
        const state = get()
        if (!state.planResult?.structured_plan) {
          return { transport: 0, attraction: 0, food: 0, hotel: 0, total: 0 }
        }

        const plan = state.planResult.structured_plan
        let transport = 0
        let attraction = 0
        let food = 0
        let hotel = 0

        // 交通：用 selected_option 或按 selected_index 获取
        if (plan.transport?.outbound) {
          const idx = plan.transport.outbound.selected_index || 0
          const outboundOpt = plan.transport.outbound.selected_option || plan.transport.outbound.options?.[idx]
          if (outboundOpt) {
            transport += outboundOpt.estimated_price || 0
          }
        }
        if (plan.transport?.return) {
          const idx = plan.transport.return.selected_index || 0
          const returnOpt = plan.transport.return.selected_option || plan.transport.return.options?.[idx]
          if (returnOpt) {
            transport += returnOpt.estimated_price || 0
          }
        }

        // 景点
        if (plan.attractions) {
          attraction = plan.attractions.reduce((sum, attr) => sum + (attr.estimated_price_value || 0), 0)
        }

        // 饮食：用 selected_option 或按 selected_index 获取
        if (plan.foods) {
          food = plan.foods.reduce((sum, meal) => {
            const idx = meal.selected_index || 0
            const mealOpt = meal.selected_option || meal.options?.[idx]
            if (mealOpt) {
              return sum + (mealOpt.estimated_price || 0)
            }
            return sum
          }, 0)
        }

        // 住宿：用 selected_option 或按 selected_index 获取
        if (plan.hotels && state.tripData.departureTime && state.tripData.returnTime) {
          const idx = plan.hotels.selected_index || 0
          const hotelOpt = plan.hotels.selected_option || plan.hotels.options?.[idx]
          if (hotelOpt) {
            const start = new Date(state.tripData.departureTime)
            const end = new Date(state.tripData.returnTime)
            const nights = Math.max(1, Math.ceil((end - start) / (1000 * 60 * 60 * 24)))
            hotel = (hotelOpt.estimated_price || 0) * nights
          }
        }

        return {
          transport: Math.round(transport),
          attraction: Math.round(attraction),
          food: Math.round(food),
          hotel: Math.round(hotel),
          total: Math.round(transport + attraction + food + hotel)
        }
      },

      registerUser: (email, password) => set((state) => {
        const exists = state.users.find((u) => u.email === email)
        if (exists) return {}

        const newUser = {
          id: String(Date.now()),
          email,
          password,
          nickname: email.split('@')[0],
          createdAt: new Date().toISOString()
        }

        return { users: [...state.users, newUser] }
      }),

      loginUser: (email, password) => {
        const state = useTripStore.getState()
        const user = state.users.find((u) => u.email === email && u.password === password)
        return user || null
      }
    }),
    {
      name: 'trip-store',
      storage: createJSONStorage(() => localStorage)
    }
  )
)