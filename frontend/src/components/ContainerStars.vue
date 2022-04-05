<template>
  <v-badge :content="localState.stars || '0'" inline class="mx-1" color="blue-grey lighten-1">
    <template v-if="isStarred()">
      <v-icon color="yellow accent-4" @click="removeStar()">mdi-star</v-icon>
    </template>
    <template v-else>
      <v-icon @click="addStar()">mdi-star-outline</v-icon>
    </template>
  </v-badge>
</template>
<script lang="ts">
import { Container } from '@/store/models';
import Vue from 'vue';
import { find as _find } from 'lodash';

interface State {
  stars: number;
}

export default Vue.extend({
  name: 'ContainerStars',
  mounted() {
    this.loadStars();
    this.localState.stars = this.container.stars;
  },
  props: {
    container: {
      type: Container,
      required: true,
    },
  },
  data: (): { localState: State } => ({
    localState: {
      stars: 0,
    }
  }),
  methods: {
    isStarred(): boolean {
      return !!_find(this.$store.getters['users/starred'], c => c.id === this.container.id);
    },
    addStar() {
      this.$store.dispatch('users/addStar', this.container)
        .then(() => {
          this.localState.stars++;
        })
        .catch(err => this.$store.commit('snackbar/showError', err));
    },
    removeStar() {
      this.$store.dispatch('users/removeStar', this.container)
        .then(() => {
          this.localState.stars--;
        })
        .catch(err => this.$store.commit('snackbar/showError', err));
    },
    loadStars() {
      this.$store.dispatch('users/getStarred')
        .catch(err => this.$store.commit('snackbar/showError', err));
    }
  },
})
</script>