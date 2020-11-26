<template>
  <v-badge :content="container.stars || '0'" inline class="mx-1" color="blue-grey lighten-1">
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

export default Vue.extend({
  name: 'ContainerStars',
  props: {
    container: {
      type: Container,
      required: true,
    },
  },
  methods: {
    isStarred(): boolean {
      return !!_find(this.$store.getters['users/starred'], c => c.id === this.container.id);
    },
    addStar() {
      this.$store.dispatch('users/addStar', this.container)
        .then(() => {
          this.container.stars++;
        })
        .catch(err => this.$store.commit('snackbar/showError', err));
    },
    removeStar() {
      this.$store.dispatch('users/removeStar', this.container)
        .then(() => {
          this.container.stars--;
        })
        .catch(err => this.$store.commit('snackbar/showError', err));
    },
  },
})
</script>